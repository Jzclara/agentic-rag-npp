"""
Agentic RAG 后端服务。
接收前端请求，调用 LangGraph 图，通过 SSE 流式返回结果。

启动方式：
  .venv/Scripts/uvicorn.exe src.server:app --reload --port 8000
"""

import json
import re
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pathlib import Path

from src.graph.app import build_graph

app = FastAPI()

# 允许前端跨域访问（开发阶段需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局初始化 ──
# 编译 LangGraph 图，全局只做一次，后续每次请求复用。
# 这一步会触发索引加载和 embedding 模型加载，首次启动会慢几秒。
graph = build_graph()


# ── 请求体定义 ──
class ChatRequest(BaseModel):
    """前端 POST /api/chat 的请求体。
    对应 api.js 里 chatStream() 发出的 JSON。"""
    question: str
    history: list = []
    selected_paper_ids: list = []
    chat_id: str | None = None


# ── 工具函数 ──
def sse_event(data: dict) -> str:
    """把一个 dict 转成 SSE 协议格式的字符串。
    SSE 规定：每条消息以 'data: ' 开头，以两个换行结尾。
    前端 api.js 里的 chatStream() 就是按这个格式解析的。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def convert_history(frontend_messages: list) -> list[dict]:
    """把前端的消息格式转成后端期望的格式。
    前端: { role: 'user', text: '...' }  /  { role: 'assistant', answer: [...] }
    后端: { role: 'user', content: '...' }  /  { role: 'assistant', content: '...' }
    """
    history = []
    for msg in frontend_messages:
        role = msg.get("role", "")
        if role == "user":
            history.append({"role": "user", "content": msg.get("text", "")})
        elif role == "assistant":
            # assistant 的 answer 是结构化数组 [{ p: "..." }, ...], 拼成纯文本
            answer = msg.get("answer", [])
            if isinstance(answer, list):
                text = "".join(part.get("p", "") for part in answer if isinstance(part, dict))
            else:
                text = str(answer)
            history.append({"role": "assistant", "content": text})
    return history


def parse_answer_to_parts(text: str) -> list[dict]:
    """把 LLM 输出的带 [1][2] 标记的文本，解析成前端需要的结构化 parts。

    输入: "BN 是概率图模型 [1]，展开后变成 DBN [3]。"
    输出: [
        {"p": "BN 是概率图模型 "},
        {"p": "[1]", "cite": 1},
        {"p": "，展开后变成 DBN "},
        {"p": "[3]", "cite": 3},
        {"p": "。"},
    ]
    """
    parts = []
    # 用正则按 [数字] 切分文本
    # re.split 保留捕获组，所以结果是 [文本, 数字, 文本, 数字, ...]
    segments = re.split(r'\[(\d+)\]', text)

    for i, seg in enumerate(segments):
        if i % 2 == 0:
            # 偶数位置是普通文本
            if seg:
                # 按换行拆分，插入 { br: true }
                lines = seg.split('\n')
                for j, line in enumerate(lines):
                    if j > 0:
                        parts.append({"br": True})
                    if line:
                        parts.append({"p": line})
        else:
            # 奇数位置是引用编号
            parts.append({"p": "", "cite": int(seg)})

    return parts if parts else [{"p": text}]


# ── 接口 ──
EVALS_DIR = Path("results/evals")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/evals")
def get_evals():
    """读取 results/evals/ 下所有评估结果 JSON，返回给前端。
    每个文件格式（由 run_ragas.py 的 save_eval_result 写入）：
      { timestamp, run_name, model, num_samples, scores: { faithfulness, answer_relevancy } }
    """
    results = []
    if EVALS_DIR.exists():
        for path in sorted(EVALS_DIR.glob("eval_*.json"), reverse=True):
            with open(path, "r", encoding="utf-8") as f:
                results.append(json.load(f))
    return {"evals": results}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """SSE 流式对话接口。

    工作流程：
      1. 用前端传来的 question/history 构造 AgentState
      2. 调用 graph.stream(state)，每个节点完成时 yield 一次
      3. 每次 yield 转成一条 SSE event 推给前端
      4. 全部节点跑完后，推送 answer 和 done
    """

    def generate():
        # ═══════════════════════════════════════════
        # 第 1 步：构造初始 AgentState
        # ═══════════════════════════════════════════
        # 这就是 graph/state.py 里定义的那个 TypedDict。
        # 每个字段会在不同节点里被填充和更新。
        state = {
            "question": req.question,
            "history": convert_history(req.history),
            "standalone_query": "",
            "contexts": [],
            "sources": [],
            "context_sufficient": False,
            "retry_count": 0,
            "max_retries": 2,
            "answer": "",
        }

        total_start = time.time()
        node_start = total_start
        retries = 0
        final_answer = ""
        final_sources = []

        # ═══════════════════════════════════════════
        # 第 2 步：逐节点执行图，并推送 SSE 事件
        # ═══════════════════════════════════════════
        # graph.stream(state) 和 graph.invoke(state) 的区别：
        #   invoke：跑完所有节点，一次性返回最终 state
        #   stream：每跑完一个节点就 yield 一次，格式 {"节点名": {输出字段}}
        #
        # 我们遍历这个 generator，每次 yield 就推一条 SSE 给前端。
        for step in graph.stream(state):
            # step 格式示例：{"rewrite": {"standalone_query": "...", "retry_count": 0}}
            node_name = list(step.keys())[0]
            node_output = step[node_name]

            # 计算这个节点执行了多少毫秒
            node_ms = int((time.time() - node_start) * 1000)
            node_start = time.time()

            # increment_retry 是辅助节点（只做计数+1），不需要推给前端
            if node_name == "increment_retry":
                retries += 1
                continue

            # ── 推 node_start ──
            # 前端收到后会点亮进度条的对应格子
            yield sse_event({"type": "node_start", "name": node_name})

            # ── 构造 node_done 事件 ──
            # 前端收到后会记录到 trace 面板（右侧 Inspector）
            evt = {
                "type": "node_done",
                "name": node_name,
                "id": f"{node_name}-{int(time.time() * 1000)}",
                "tag": "Hybrid" if node_name == "retrieve" else "LLM",
                "ms": node_ms,
                "detail": "",
            }

            # 根据节点类型，填充不同的 detail 信息
            if node_name == "rewrite":
                sq = node_output.get("standalone_query", "")
                evt["detail"] = f"改写为：{sq}"
                evt["quote"] = sq

            elif node_name == "retrieve":
                n = len(node_output.get("contexts", []))
                final_sources = node_output.get("sources", [])
                evt["detail"] = f"混合检索，返回 {n} 个片段。"
                evt["subnodes"] = [
                    "向量召回 · top-10",
                    "BM25 召回 · top-10",
                    "RRF 融合 · k=60",
                    "Cross-encoder 重排 · top-5",
                ]

            elif node_name == "grade":
                ok = node_output.get("context_sufficient", False)
                evt["verdict"] = "relevant" if ok else "insufficient"
                evt["detail"] = (
                    "上下文相关 → 进入生成。" if ok
                    else "上下文不足 → 触发重试。"
                )
                if not ok:
                    evt["retry"] = True

            elif node_name == "generate":
                final_answer = node_output.get("answer", "")
                evt["detail"] = "已生成回答。"

            elif node_name == "fallback":
                final_answer = node_output.get("answer", "")
                evt["detail"] = "检索不足，走兜底回答。"

            yield sse_event(evt)

        # ═══════════════════════════════════════════
        # 第 3 步：推送答案
        # ═══════════════════════════════════════════
        # parse_answer_to_parts 把 "文本 [1] 文本 [2]" 解析成前端的结构化格式。
        # final_sources 是 retrieve 节点提取的元数据（文件名、页码、原文摘录）。
        yield sse_event({
            "type": "answer",
            "parts": parse_answer_to_parts(final_answer),
            "sources": final_sources,
        })

        # ═══════════════════════════════════════════
        # 第 4 步：推送完成信号
        # ═══════════════════════════════════════════
        total_ms = int((time.time() - total_start) * 1000)
        yield sse_event({
            "type": "done",
            "totalMs": total_ms,
            "tokens": 0,
            "retries": retries,
        })

    return StreamingResponse(generate(), media_type="text/event-stream")
