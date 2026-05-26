"""
Agentic RAG 的状态定义。

LangGraph 的每个节点共享同一个状态对象，节点从中读取数据、处理后更新。
可以理解为一张在节点之间流转的表单，每个节点填写自己负责的字段。
"""

from typing import TypedDict


class AgentState(TypedDict):
    # ── 输入 ──
    question: str                    # 用户原始问题（每轮对话的输入）
    history: list[dict[str, str]]    # 对话历史，格式 [{"role": "user", "content": "..."}, ...]

    # ── 检索相关 ──
    standalone_query: str            # rewrite 节点输出：将多轮问题改写为独立查询
    contexts: list[str]              # retrieve 节点输出：检索到的文档片段列表
    context_sufficient: bool         # grade 节点输出：检索内容是否足够回答问题

    # ── 控制流 ──
    retry_count: int                 # 当前已重试次数（每次检索不足时 +1）
    max_retries: int                 # 最大重试次数（超过则走 fallback 兜底）

    # ── 引用来源 ──
    sources: list[dict]              # retrieve 节点输出：每个检索片段的元数据（文件名、页码、原文摘录）

    # ── 输出 ──
    answer: str                      # generate 或 fallback 节点输出：最终回答