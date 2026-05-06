import json
from datetime import datetime
from pathlib import Path

from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from src.config import ZHIPU_API_KEY, ZHIPU_BASE_URL,ZHIPU_MODEL
from src.indexing.build_index import build_index
from src.indexing.retriever import get_retriever, retrieve, get_contexts

RESULTS_DIR = "results/runs"

def setup_llm():
    # 使用 Zhipu 的 OpenAI 兼容接口初始化 LLM
    Settings.llm = OpenAI(
        model=ZHIPU_MODEL,
        api_key=ZHIPU_API_KEY,
        api_base=ZHIPU_BASE_URL,
    )

def generate_answer(query: str, contexts: list[str]) -> str:
    context_str = "\n\n".join(contexts)
    prompt = (
        f"Answer the question based only on the context below.\n\n"
        f"Context:\n{context_str}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )
    response = Settings.llm.complete(prompt)
    return str(response)

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
    setup_llm()
    index = build_index()
    retriever = get_retriever(index)
    nodes = retrieve(retriever,query)
    contexts = get_contexts(nodes)
    answer = generate_answer(query, contexts)
    save_result(query, contexts, answer)
    print(f"\nQuestion: {query}")
    print(f"\nAnswer: {answer}")
    return answer


if __name__ == "__main__":
    run("What methods are used for fault diagnosis in nuclear power plants?")