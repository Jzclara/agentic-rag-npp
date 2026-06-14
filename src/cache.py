"""
Redis 缓存层（阶段 ③）。

作用：给「又慢又贵」的 RAG 流程加一层内存缓存。
  - 收到问题 → 先查 Redis
  - 命中  → 直接返回上次的最终结果（answer / sources / eval），跳过整条 LangGraph 图，毫秒级、不花 LLM 钱
  - 未命中 → 跑完整流程 → 把结果写回 Redis（带 TTL，自动过期防陈旧）

设计取舍：
  - 缓存键 = hash(question + 选中的 paper_ids)，不含对话历史。
    带历史几乎不会命中，且历史会改变答案语义，所以「带上下文的追问」一律不走缓存（见 server.py：history 非空时跳过）。
  - 只缓存「最终结果」（A+ 方案），命中时由 server 重放 answer/eval/done 三条事件，
    并明确标记 cached=true，让前端展示「⚡ 缓存命中」，而不是伪造中间节点动画。
  - Redis 不可用时所有函数静默降级（返回 None / 不写），绝不影响主流程。

连接信息来自环境变量 REDIS_URL（容器里连服务名 redis，本地连 localhost）。
"""

import hashlib
import json

try:
    import redis
except ImportError:
    # 没装 redis 库时整体降级关闭，不影响后端启动（容器里已在 requirements 装好）。
    redis = None

from src.config import REDIS_URL, CACHE_TTL

# 全局客户端：懒连接（decode_responses=True 让读写都用 str，省得手动 encode/decode）。
# 连接错误在使用时捕获，模块导入阶段不会因 Redis 没起来而报错。
_client: "redis.Redis | None" = None
# 首次连接失败后置位，避免之后每个请求都再等一次连接超时（拖慢主流程）。
_disabled = False


def _get_client() -> "redis.Redis | None":
    """获取全局 Redis 客户端，首次调用时建立连接。任何连接异常都降级为 None 并永久关闭缓存。"""
    global _client, _disabled
    if redis is None or _disabled:
        return None
    if _client is None:
        try:
            _client = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            _client.ping()
        except Exception as e:
            print(f"[cache] Redis 连接失败，缓存降级关闭：{e}")
            _client = None
            _disabled = True
    return _client


def make_key(question: str, selected_paper_ids: list | None) -> str:
    """根据问题 + 选中的 paper 范围生成稳定缓存键。
    paper_ids 排序后参与哈希，保证「选中范围相同、顺序不同」也命中同一个键。"""
    ids = sorted(selected_paper_ids or [])
    raw = json.dumps({"q": question.strip(), "ids": ids}, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"chat:answer:{digest}"


def get_cached(key: str) -> dict | None:
    """读缓存。命中返回 dict（之前 set_cached 存的 payload），未命中/异常返回 None。"""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        print(f"[cache] 读取失败：{e}")
        return None


def set_cached(key: str, payload: dict, ttl: int = CACHE_TTL) -> None:
    """写缓存，带 TTL（秒）过期。异常静默忽略，不影响主流程。"""
    client = _get_client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl)
    except Exception as e:
        print(f"[cache] 写入失败：{e}")
