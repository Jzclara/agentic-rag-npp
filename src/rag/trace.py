import json
from datetime import datetime
from pathlib import Path

from src.config import LLM_MODEL

RESULTS_DIR = Path("results/runs")

def save_turn_result(
    run_name: str,
    turn: int,
    user_input: str,
    standalone_query: str,
    contexts: list[str],
    sources: list[dict],
    answer: str,
) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "timestamp": timestamp,
        "run_name": run_name,
        "model": LLM_MODEL,
        "turn": turn,
        "user_input": user_input,
        "standalone_query": standalone_query,
        "retrieved_contexts": contexts,
        "sources": sources,
        "answer": answer,
    }

    output_path = RESULTS_DIR / f"mulchat_{date_id}_{run_name}_turn{turn:03d}.json"


    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return output_path

