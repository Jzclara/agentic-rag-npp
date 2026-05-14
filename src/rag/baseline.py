import json
from datetime import datetime
from pathlib import Path

from src.indexing.build_index import build_index
from src.indexing.retriever import get_retriever, retrieve, get_contexts
from src.llm import setup_llm
from src.rag.generation import generate_answer

RESULTS_DIR = "results/runs"

def save_result(query: str, contexts: list[str], answer: str):
    # 保存每次运行结果，供第二阶段 Ragas 评估直接读取
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "user_input": query,
        "retrieved_contexts": contexts,
        "answer" : answer
    }
    output_path = Path(RESULTS_DIR) / f"{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Result saved to {output_path}")

def run(query: str):
    client = setup_llm()
    index = build_index()
    retriever = get_retriever(index)
    nodes = retrieve(retriever,query)
    contexts = get_contexts(nodes)
    answer = generate_answer(client, query, contexts)
    save_result(query, contexts, answer)
    print(f"\nQuestion: {query}")
    print(f"\nAnswer: {answer}")
    return answer


if __name__ == "__main__":
    run("What methods are used for fault diagnosis in nuclear power plants?")
