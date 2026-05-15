import json
from datetime import datetime
from pathlib import Path

from src.config import LLM_MODEL

RESULTS_DIR = Path("results/runs")


def save_session(
    run_name: str,
    turns: list[dict],
) -> Path:
    """对话结束后，把整个会话的所有轮次保存为一个文件。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "timestamp": timestamp,
        "run_name": run_name,
        "model": LLM_MODEL,
        "total_turns": len(turns),
        "turns": turns,
    }

    output_path = RESULTS_DIR / f"mulchat_{timestamp}_{run_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return output_path
