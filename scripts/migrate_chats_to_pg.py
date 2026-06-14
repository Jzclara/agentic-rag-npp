"""
一次性迁移脚本：把 results/chats/*.json 导入 PostgreSQL（阶段 ②）。

用法（本地或容器内皆可，连同一个库即可）：
    python -m scripts.migrate_chats_to_pg

特性：
  - 幂等：对每个对话「先删旧消息再重插」，重复跑不会产生重复数据。
  - 保真：整条消息原样写入 messages.data（JSONB），富结构一字不丢。
  - 时间：尽量沿用文件里的 updated_at，对话列表顺序与原来一致。
"""

import json
from datetime import datetime
from pathlib import Path

from psycopg.types.json import Jsonb

from src import db

CHATS_DIR = Path("results/chats")


def _parse_updated_at(value: str):
    """把文件里的 'YYYY-MM-DD HH:MM:SS' 字符串解析为 datetime；解析失败则返回 None。"""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def migrate() -> None:
    db.init_db()

    if not CHATS_DIR.exists():
        print(f"目录不存在，无可迁移数据：{CHATS_DIR}")
        return

    files = sorted(CHATS_DIR.glob("*.json"))
    if not files:
        print(f"没有找到任何对话 JSON：{CHATS_DIR}")
        return

    total_chats = 0
    total_messages = 0

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chat_id = data.get("chat_id") or path.stem
        title = data.get("title", "未命名对话")
        messages = data.get("messages", [])
        updated_at = _parse_updated_at(data.get("updated_at", ""))

        with db.pool.connection() as conn:
            # upsert 对话；有 updated_at 就用文件里的，否则交给默认 now()。
            if updated_at is not None:
                conn.execute(
                    """
                    INSERT INTO chats (id, title, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                        SET title = EXCLUDED.title,
                            updated_at = EXCLUDED.updated_at
                    """,
                    (chat_id, title, updated_at),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO chats (id, title)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO UPDATE
                        SET title = EXCLUDED.title
                    """,
                    (chat_id, title),
                )

            # 幂等：先清掉该对话旧消息，再按顺序重插。
            conn.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))

            for seq, msg in enumerate(messages):
                conn.execute(
                    """
                    INSERT INTO messages (chat_id, seq, role, msg_id, data)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (chat_id, seq, msg.get("role", ""), msg.get("id"),
                     Jsonb(db._strip_nulls(msg))),
                )

        total_chats += 1
        total_messages += len(messages)
        print(f"  迁移 {chat_id}：{len(messages)} 条消息")

    print(f"\n完成：共迁移 {total_chats} 个对话，{total_messages} 条消息。")


if __name__ == "__main__":
    migrate()
