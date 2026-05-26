"""
Agentic RAG 的节点函数。

每个节点接收完整的 AgentState，执行一个步骤，返回需要更新的字段。
节点之间的执行顺序由 app.py 中的图编排决定，这里只关注每个节点自己做什么。
"""

from src.graph.state import AgentState
from src.indexing.build_index import build_index, build_parent_child_index
from src.indexing.retriever import (
    get_retriever, retrieve, get_contexts, get_parent_contexts,
    rerank_nodes, setup_bm25, hybrid_retrieve,
)
from src.llm import setup_llm
from src.config import LLM_MODEL, RETRIEVER_COARSE_TOP_K
from src.rag.generation import generate_answer_with_history, rewrite_query_with_history

# ── 全局初始化（只在第一次 import 时执行一次） ──

_client = None
_retriever = None

def _ensure_initialized():
    """懒加载：首次调用时初始化 LLM 客户端和检索器，后续复用。
    避免每个节点重复加载模型和索引。"""
    global _client, _retriever
    if _client is None:
        _client = setup_llm()
    if _retriever is None:
        index = build_index()
        _retriever = get_retriever(index, top_k=RETRIEVER_COARSE_TOP_K)

# ── 节点 1：改写问题 ──
def rewrite_node(state: AgentState) -> dict:
    """用对话历史改写用户问题，解析指代词。
    例如 "What are their limitations?" → "What are the limitations of Bayesian networks?"
    首次进入时 retry_count 初始化为 0。"""
    _ensure_initialized()
    standalone_query = rewrite_query_with_history(
        _client, state["question"], state["history"]
    )
    print(f"  [rewrite] {state['question']} → {standalone_query}")
    return {
        "standalone_query": standalone_query,
        "retry_count": state.get("retry_count", 0),
    }


# ── 节点 2：检索文档 ──
def retrieve_node(state: AgentState) -> dict:
    """粗召回 top-k 个候选片段，再用 cross-encoder rerank 精排取 top-n。"""
    _ensure_initialized()
    nodes = retrieve(_retriever, state["standalone_query"])
    coarse_count = len(nodes)
    nodes = rerank_nodes(state["standalone_query"], nodes)
    contexts = get_contexts(nodes)
    print(f"  [retrieve] 粗召回 {coarse_count} → rerank 后 {len(contexts)} 个片段")
    return {"contexts": contexts}


# ── 节点 3：判断检索质量 ──

def grade_node(state: AgentState) -> dict:
    """让 LLM 判断检索到的内容是否和用户问题相关。
    判断标准故意放宽：只要包含相关信息就放行，只拦截完全不相关的情况。
    之前用"sufficient"标准太严格，导致频繁误触重试，反而降低回答质量。"""
    _ensure_initialized()
    contexts_str = "\n\n".join(state["contexts"])
    prompt = (
        "You are a relevance filter. Given the user question and the retrieved context, "
        "determine if the context contains ANY information relevant to the question.\n"
        "Even partial or indirect relevance counts as 'yes'.\n"
        "Only reply 'no' if the context is completely unrelated to the question.\n"
        "Reply with only 'yes' or 'no'.\n\n"
        f"Question: {state['standalone_query']}\n\n"
        f"Context:\n{contexts_str}\n\n"
        "Does the context contain information relevant to the question?"
    )
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": "You are a relevance filter. Reply 'yes' unless the context is completely unrelated. When in doubt, reply 'yes'."},
            {"role": "user", "content": prompt},
        ],
    )
    # 防御：API 可能返回 None（网络超时、速率限制等），此时默认视为"足够"，避免误触重试
    if response is None or not response.choices:
        print("  [grade] API 返回为空，默认视为足够")
        return {"context_sufficient": True}
    answer = (response.choices[0].message.content or "").strip().lower()
    sufficient = answer.startswith("yes")
    print(f"  [grade] 检索质量: {'足够' if sufficient else '不足'}")
    return {"context_sufficient": sufficient}

# ── 节点 4：生成回答 ──

def generate_node(state: AgentState) -> dict:
    """基于检索上下文和对话历史生成最终回答。"""
    _ensure_initialized()
    answer = generate_answer_with_history(
        _client, state["question"], state["contexts"], state["history"]
    )
    print(f"  [generate] 已生成回答")
    return {"answer": answer}


# ── 节点 5：兜底回答 ──


def fallback_node(state: AgentState) -> dict:
    """重试次数用完仍检索不足时，给出兜底回答。
    不瞎编，直接告诉用户信息不够。"""
    print(f"  [fallback] 重试 {state['retry_count']} 次后仍检索不足，走兜底")
    return {
        "answer": (
            "I'm sorry, I couldn't find enough relevant information in the documents "
            "to answer your question. Could you try rephrasing or asking a more specific question?"
        )
    }


# ══════════════════════════════════════════════════════════════
# Parent-Child 版节点
# 和上面的原版节点独立，使用 parent-child 索引 + 返回 parent 上下文。
# 如需启用，在 app.py 中把 graph.add_node("retrieve", ...) 替换为
# retrieve_parent_child_node 即可，其他节点不用改。
# ══════════════════════════════════════════════════════════════

_pc_retriever = None


def _ensure_pc_initialized():
    """懒加载 parent-child 版检索器。
    LLM 客户端和原版共用，只有索引和检索器是独立的。"""
    global _client, _pc_retriever
    if _client is None:
        _client = setup_llm()
    if _pc_retriever is None:
        index = build_parent_child_index()
        _pc_retriever = get_retriever(index, top_k=RETRIEVER_COARSE_TOP_K)


def retrieve_parent_child_node(state: AgentState) -> dict:
    """Parent-Child 版检索节点。
    流程：粗召回 child 小块 → rerank 精排 → 从 metadata 取 parent 大块作为上下文。
    和原版 retrieve_node 的区别：
    - 原版：检索 512 chunk，直接用 chunk 文本
    - 本版：检索 256 child，返回对应的 1024 parent 文本，上下文更完整"""
    _ensure_pc_initialized()
    nodes = retrieve(_pc_retriever, state["standalone_query"])
    coarse_count = len(nodes)
    nodes = rerank_nodes(state["standalone_query"], nodes)
    contexts = get_parent_contexts(nodes)
    print(
        f"  [retrieve-pc] 粗召回 {coarse_count} 个 child "
        f"→ rerank 后 {len(nodes)} 个 child "
        f"→ 去重后 {len(contexts)} 个 parent 上下文"
    )
    return {"contexts": contexts}


# ══════════════════════════════════════════════════════════════
# Hybrid Search 版节点
# 向量检索 + BM25 关键词检索两路召回，RRF 合并后再 rerank。
# 如需启用，在 app.py 中把 graph.add_node("retrieve", ...) 替换为
# retrieve_hybrid_node 即可，其他节点不用改。
# ══════════════════════════════════════════════════════════════

_hybrid_retriever = None
_hybrid_index = None  # 需要保留索引引用，供 BM25 从 docstore 提取 chunk


def _ensure_hybrid_initialized():
    """懒加载混合检索所需的组件：
    1. LLM 客户端（和其他版本共用）
    2. 向量检索器（从已有索引构建）
    3. BM25 索引（从同一个索引的 docstore 提取 chunk 文本构建）"""
    global _client, _hybrid_retriever, _hybrid_index
    if _client is None:
        _client = setup_llm()
    if _hybrid_retriever is None:
        _hybrid_index = build_index()
        _hybrid_retriever = get_retriever(_hybrid_index, top_k=RETRIEVER_COARSE_TOP_K)
        # BM25 从同一个索引的 docstore 里取 chunk，不需要额外的索引文件
        setup_bm25(_hybrid_index)


def retrieve_hybrid_node(state: AgentState) -> dict:
    """Hybrid Search 版检索节点。
    流程：向量 + BM25 两路召回 → RRF 合并 → rerank 精排 → 取 top-n。
    和原版 retrieve_node 的区别：
    - 原版：只有向量检索一条路
    - 本版：向量 + BM25 两路互补，精确术语和语义相似都能覆盖

    返回 contexts（纯文本，给 LLM 用）和 sources（元数据，给前端引用面板用）。"""
    _ensure_hybrid_initialized()

    # 第一步：两路召回 + RRF 合并
    fused_nodes = hybrid_retrieve(state["standalone_query"], _hybrid_retriever)
    fused_count = len(fused_nodes)

    # 第二步：rerank 精排
    nodes = rerank_nodes(state["standalone_query"], fused_nodes)
    contexts = get_contexts(nodes)

    # 第三步：提取元数据，供前端引用面板展示
    sources = []
    for i, node in enumerate(nodes, start=1):
        meta = node.node.metadata
        sources.append({
            "n": i,
            "fileName": meta.get("file_name", "unknown"),
            "page": meta.get("page_label", "?"),
            "score": round(node.score, 3) if node.score else 0,
            "quote": node.node.text[:200],  # 取前 200 字作为卡片列表摘录
            "full_text": node.node.text,    # 完整 chunk 文本，供弹窗展示
        })

    print(
        f"  [retrieve-hybrid] RRF 合并 {fused_count} 个候选 "
        f"→ rerank 后 {len(contexts)} 个片段"
    )
    return {"contexts": contexts, "sources": sources}