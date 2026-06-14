"""
Agentic RAG 图编排。

把 nodes.py 中的节点连成 LangGraph 状态图：
  rewrite → retrieve → grade → generate（检索足够时）
                             → rewrite 重试（检索不足时）
                             → fallback 兜底（重试次数用完时）
"""
from langgraph.graph import StateGraph, END

from src.graph.state import AgentState
from src.graph.nodes import (
    rewrite_node,
    retrieve_node,
    grade_node,
    generate_node,
    fallback_node,
    retrieve_parent_child_node,
    retrieve_hybrid_node
)

def route_after_grade(state: AgentState) -> str:
    """grade_node 之后的路由函数。
    根据检索质量和重试次数，决定走哪条路：
      - 检索足够 → 去 generate 生成回答
      - 检索不足但还能重试 → 回 rewrite 改写后重新检索
      - 重试次数用完 → 去 fallback 兜底"""
    if state["context_sufficient"]:
        return "generate"
    if state["retry_count"] < state.get("max_retries", 2):
        return "rewrite"
    return "fallback"

def increment_retry(state: AgentState) -> dict:
    """重试前把 retry_count 加 1。
    这是一个辅助节点，不做实际业务逻辑。"""
    return {"retry_count": state["retry_count"] + 1}

# ── 构建图 ──


RETRIEVE_NODES = {
    "vector":       retrieve_node,                # 纯向量 + Rerank
    "parent_child": retrieve_parent_child_node,   # Parent-Child + Rerank
    "hybrid":       retrieve_hybrid_node,          # Hybrid（向量 + BM25 + RRF）+ Rerank
}


def build_graph(retriever_type: str = "hybrid"):
    """构建并返回编译好的 Agentic RAG 图。
    retriever_type: "vector" | "parent_child" | "hybrid"（默认 hybrid）"""
    if retriever_type not in RETRIEVE_NODES:
        raise ValueError(f"未知的检索策略：{retriever_type}，可选：{list(RETRIEVE_NODES.keys())}")

    graph = StateGraph(AgentState)

    # 注册节点：名字 → 函数
    graph.add_node("rewrite", rewrite_node)              # 改写问题，解析指代词
    graph.add_node("retrieve", RETRIEVE_NODES[retriever_type])
    graph.add_node("grade", grade_node)                  # 让 LLM 判断检索内容是否足够
    graph.add_node("generate", generate_node)            # 检索足够时，生成最终回答
    graph.add_node("fallback", fallback_node)            # 重试用完仍不足时，给兜底回答
    graph.add_node("increment_retry", increment_retry)   # 辅助节点：重试计数 +1，防止无限循环

    # 设置入口：从 rewrite 开始
    graph.set_entry_point("rewrite")

    # 固定边：这三步总是顺序执行
    graph.add_edge("rewrite", "retrieve")    # 改写完 → 去检索
    graph.add_edge("retrieve", "grade")      # 检索完 → 去判断质量

    # 条件边：grade 之后根据判断结果走不同路径
    graph.add_conditional_edges("grade", route_after_grade, {
        "generate": "generate",       # 检索足够 → 生成回答
        "rewrite": "increment_retry", # 检索不足 → 先加重试计数再回 rewrite
        "fallback": "fallback",       # 重试用完 → 兜底
    })

    # increment_retry 之后回到 rewrite，形成重试循环
    graph.add_edge("increment_retry", "rewrite")

    # 终点：generate 和 fallback 执行完，流程结束
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)

    return graph.compile()

