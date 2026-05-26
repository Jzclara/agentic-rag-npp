from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

from src.config import (
    RERANKER_MODEL, RERANKER_TOP_N, BGE_CACHE_DIR,
    BM25_TOP_K, RRF_K, RETRIEVER_COARSE_TOP_K,
)


def get_retriever(index: VectorStoreIndex, top_k: int = 5):
    # as_retriever 把索引包装成检索器，检索时返回相似度最高的 top_k 个 chunk
    return index.as_retriever(similarity_top_k=top_k)

def retrieve(retriever, query: str) -> list[NodeWithScore]:
    # 每个 NodeWithScore 包含 node.text（chunk 文本）和 score（相似度分数）
    nodes = retriever.retrieve(query)
    return nodes

def get_contexts(nodes: list[NodeWithScore]) -> list[str]:
    # 把 NodeWithScore 列表转成纯文本列表，方便传给 LLM 和 Ragas 评估
    return [node.node.text for node in nodes]

def get_sources(nodes: list[NodeWithScore]) -> list[dict]:
    sources = []

    for node in nodes:
        metadata = node.node.metadata
        sources.append(
            {
                "file_name": metadata.get("file_name", "unknown file"),
                "page_label": metadata.get("page_label", "unknown page"),
                "score": node.score,
            }
        )

    return sources


# ── Rerank ──

_reranker: CrossEncoder | None = None


def setup_reranker() -> CrossEncoder:
    """懒加载 cross-encoder reranker，首次调用时加载模型，后续复用。"""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def rerank_nodes(
    query: str,
    nodes: list[NodeWithScore],
    top_n: int = RERANKER_TOP_N,
) -> list[NodeWithScore]:
    """用 cross-encoder 对粗召回结果重新打分排序，取 top_n 个。
    cross-encoder 同时看 query 和 chunk，比向量余弦相似度更准。"""
    reranker = setup_reranker()
    pairs = [[query, node.node.text] for node in nodes]
    scores = reranker.predict(pairs)

    scored = sorted(zip(nodes, scores), key=lambda x: x[1], reverse=True)
    result = []
    for node, new_score in scored[:top_n]:
        node.score = float(new_score)
        result.append(node)
    return result


# ── Parent-Child 上下文提取 ──


# ── Hybrid Search（混合检索） ──
# 向量检索 + BM25 关键词检索两路召回，用 RRF 合并结果。
# 向量擅长语义匹配，BM25 擅长精确关键词匹配，互补短板。

_bm25: BM25Okapi | None = None
_bm25_nodes: list | None = None  # BM25 语料库对应的节点列表，用于把 BM25 分数映射回节点


def setup_bm25(index: VectorStoreIndex) -> BM25Okapi:
    """从索引的 docstore 中提取所有 chunk 文本，构建 BM25 索引。
    BM25 不需要 embedding，它用词频统计做关键词匹配。
    只需构建一次，后续复用。"""
    global _bm25, _bm25_nodes
    if _bm25 is not None:
        return _bm25

    # 从 docstore 取出所有节点（和向量索引里的是同一批 chunk）
    docstore = index.docstore
    _bm25_nodes = list(docstore.docs.values())

    # 分词：对英文学术论文，简单按空格切分 + 转小写就够用
    tokenized = [node.get_content().lower().split() for node in _bm25_nodes]

    _bm25 = BM25Okapi(tokenized)
    print(f"BM25 索引构建完成，共 {len(_bm25_nodes)} 个 chunk")
    return _bm25


def bm25_retrieve(query: str, top_k: int = BM25_TOP_K) -> list[NodeWithScore]:
    """用 BM25 关键词匹配检索 top_k 个最相关的 chunk。
    和向量检索不同，BM25 看的是问题和 chunk 之间的关键词重叠程度。"""
    if _bm25 is None or _bm25_nodes is None:
        raise RuntimeError("BM25 未初始化，请先调用 setup_bm25()")

    # 对查询做和语料库相同的分词处理
    tokenized_query = query.lower().split()
    scores = _bm25.get_scores(tokenized_query)

    # 按 BM25 分数降序取 top_k
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    result = []
    for idx in top_indices:
        node = _bm25_nodes[idx]
        result.append(NodeWithScore(node=node, score=float(scores[idx])))
    return result


def rrf_fuse(
    vector_nodes: list[NodeWithScore],
    bm25_nodes: list[NodeWithScore],
    k: int = RRF_K,
    top_n: int = RETRIEVER_COARSE_TOP_K,
) -> list[NodeWithScore]:
    """Reciprocal Rank Fusion：合并两路检索结果。
    对每个 chunk 计算 RRF 得分 = Σ 1/(k + rank)，两路都排前面的得分最高。
    k 是常数（默认 60），用于压平排名差距。"""
    rrf_scores: dict[str, float] = {}   # node_id → 累加的 RRF 得分
    node_map: dict[str, NodeWithScore] = {}  # node_id → 节点对象（去重用）

    # 向量检索结果的 RRF 贡献
    for rank, node in enumerate(vector_nodes, start=1):
        node_id = node.node.node_id
        rrf_scores[node_id] = rrf_scores.get(node_id, 0) + 1 / (k + rank)
        node_map[node_id] = node

    # BM25 检索结果的 RRF 贡献
    for rank, node in enumerate(bm25_nodes, start=1):
        node_id = node.node.node_id
        rrf_scores[node_id] = rrf_scores.get(node_id, 0) + 1 / (k + rank)
        if node_id not in node_map:
            node_map[node_id] = node

    # 按 RRF 得分降序排列，取 top_n
    sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_n]

    result = []
    for node_id in sorted_ids:
        node = node_map[node_id]
        node.score = rrf_scores[node_id]
        result.append(node)
    return result


def hybrid_retrieve(
    query: str,
    vector_retriever,
    bm25_top_k: int = BM25_TOP_K,
    rrf_k: int = RRF_K,
    fuse_top_n: int = RETRIEVER_COARSE_TOP_K,
) -> list[NodeWithScore]:
    """混合检索入口：向量 + BM25 两路召回 → RRF 合并。
    返回合并后的 top_n 个候选，可以再接 rerank 做精排。"""
    # 两路同时检索
    vector_nodes = retrieve(vector_retriever, query)
    bm25_nodes = bm25_retrieve(query, top_k=bm25_top_k)

    # RRF 合并
    fused = rrf_fuse(vector_nodes, bm25_nodes, k=rrf_k, top_n=fuse_top_n)

    print(
        f"    [hybrid] 向量召回 {len(vector_nodes)} + BM25 召回 {len(bm25_nodes)} "
        f"→ RRF 合并后 {len(fused)} 个候选"
    )
    return fused


# ── Parent-Child 上下文提取 ──


def get_parent_contexts(nodes: list[NodeWithScore]) -> list[str]:
    """从检索到的 child 节点的 metadata 中取出 parent 完整文本。
    多个 child 可能属于同一个 parent，自动去重避免重复上下文。
    如果某个 node 没有 parent_text（比如用普通索引检索的），回退到 node 自身文本。"""
    seen = set()
    contexts = []
    for node in nodes:
        parent_text = node.node.metadata.get("parent_text", node.node.text)
        text_hash = hash(parent_text)
        if text_hash not in seen:
            seen.add(text_hash)
            contexts.append(parent_text)
    return contexts
