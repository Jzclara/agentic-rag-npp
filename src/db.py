"""
PostgreSQL 持久化层（阶段 ②）。

把聊天记录从「一个对话一个 JSON 文件」升级为「关系数据库」：
  - chats   ：对话表
  - messages：消息表，与 chats 一对多（外键 + 级联删除）

设计取舍（关系 + JSONB 混合）：
  - 需要查询/排序的字段（role、seq、updated_at…）提到独立列上，可加索引、可 SQL 过滤；
  - assistant 消息的富结构（answer / sources / trace / timing…）整条原样存进
    `messages.data` 这个 JSONB 列，前端字段零丢失、零改动。

连接信息来自环境变量 DATABASE_URL（容器里连服务名 db，本地连 localhost）。
"""

import os
import time

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

# 本地默认值仅用于开发；容器里由 docker-compose 注入 DATABASE_URL。
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rag:rag_pwd@localhost:5432/ragdb",
)

# 全局连接池：复用连接、并发安全。open=False 表示先不连，等首次用时再建立，
# 避免模块导入时数据库还没起来就报错。
pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=10, open=False)


# ── 建表 ──
SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT '未命名对话',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,
    role        TEXT NOT NULL,
    msg_id      TEXT,
    data        JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id, seq);
"""


def init_db() -> None:
    """打开连接池并建表（幂等）。服务启动时调用一次。"""
    pool.open()
    with pool.connection() as conn:
        conn.execute(SCHEMA)


def _fmt(ts) -> str:
    """把 TIMESTAMPTZ 格式化成前端一直在用的 'YYYY-MM-DD HH:MM:SS' 字符串。"""
    if ts is None:
        return ""
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _strip_nulls(obj):
    """递归移除字符串里的 \\u0000（空字符）。

    PostgreSQL 的 JSONB 不支持 \\u0000，而 PDF 抽取出来的文本偶尔带这种控制字符，
    不清掉会导致写库报 UntranslatableCharacter。"""
    if isinstance(obj, str):
        return obj.replace("\x00", "")
    if isinstance(obj, list):
        return [_strip_nulls(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items()}
    return obj


# ── 4 个数据访问函数（对应 server.py 的 4 个接口）──


def db_list_chats() -> list[dict]:
    """列出所有对话，按更新时间倒序，只返回摘要信息。"""
    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id,
                   c.title,
                   c.updated_at,
                   (SELECT count(*) FROM messages m WHERE m.chat_id = c.id) AS message_count
            FROM chats c
            ORDER BY c.updated_at DESC
            """
        ).fetchall()

    return [
        {
            "id": row[0],
            "title": row[1] or "未命名对话",
            "message_count": row[3],
            "updated_at": _fmt(row[2]),
        }
        for row in rows
    ]


def db_load_chat(chat_id: str) -> dict:
    """加载某个对话的完整消息记录（结构与原 JSON 文件一致）。"""
    with pool.connection() as conn:
        chat = conn.execute(
            "SELECT id, title, updated_at FROM chats WHERE id = %s",
            (chat_id,),
        ).fetchone()

        if chat is None:
            return {"chat_id": chat_id, "title": "", "messages": []}

        rows = conn.execute(
            "SELECT data FROM messages WHERE chat_id = %s ORDER BY seq",
            (chat_id,),
        ).fetchall()

    return {
        "chat_id": chat[0],
        "title": chat[1],
        "messages": [row[0] for row in rows],
        "updated_at": _fmt(chat[2]),
    }


def db_save_chat(chat_id: str, title: str, messages: list) -> None:
    """保存/更新一个对话（全量覆盖语义，与前端协议一致）。

    整个操作在一个事务里完成，保证一致性：
      1. upsert 对话（存在则更新 title 和 updated_at）
      2. 删掉该对话的旧消息
      3. 按顺序重新插入新消息
    """
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    # `with pool.connection()` 退出时自动提交（出错则回滚），天然就是一个事务。
    with pool.connection() as conn:
        conn.execute(
            """
            INSERT INTO chats (id, title, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET title = EXCLUDED.title,
                    updated_at = EXCLUDED.updated_at
            """,
            (chat_id, title, now),
        )

        conn.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))

        for seq, msg in enumerate(messages):
            conn.execute(
                """
                INSERT INTO messages (chat_id, seq, role, msg_id, data)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    chat_id,
                    seq,
                    msg.get("role", ""),
                    msg.get("id"),
                    Jsonb(_strip_nulls(msg)),
                ),
            )


def db_delete_chat(chat_id: str) -> None:
    """删除一个对话（外键 ON DELETE CASCADE 会自动删掉其消息）。"""
    with pool.connection() as conn:
        conn.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
