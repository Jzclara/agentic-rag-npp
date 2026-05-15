import json
from pathlib import Path
<<<<<<< HEAD

RUNS_DIR = Path("results/runs")

def load_mulchat_records(run_name: str | None = None) -> list[dict]:
    records = []
    #扫描 results/runs/ 下面所有 mulchat_*.json
    #读取每个 JSON
    for path in sorted(RUNS_DIR.glob("mulchat_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        #run_name 是实验名称过滤器。
        # 不传 = 读取所有实验。
        # 传了 = 只读取这个实验。
        if run_name is not None and record.get("run_name") != run_name:
            continue

        records.append(record)

    return records

def build_ragas_samples(records: list[dict]) -> list[dict]:
    samples = []

    for record in records:
        sample = {
            "question": record["standalone_query"],
            "answer": record["answer"],
            "contexts": record["retrieved_contexts"],
        }
        samples.append(sample)

    return samples

#能不能读到 mulchat 日志
#能不能转成 question / answer / contexts
#contexts 数量对不对
def main():
    records = load_mulchat_records(run_name="deep_test1")
    samples = build_ragas_samples(records)

    print(f"Loaded records: {len(records)}")
    print(f"Built samples: {len(samples)}")

    if samples:
        first = samples[0]
        print("\nFirst sample:")
        print(f"Question: {first['question']}")
        print(f"Answer: {first['answer'][:300]}...")
        print(f"Contexts: {len(first['contexts'])}")
=======
from openai import OpenAI as OpenAIClient
from ragas.llms import llm_factory
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from src.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    BGE_EMBEDDING_MODEL,
    BGE_CACHE_DIR,
)
from datasets import Dataset
from ragas import evaluate
from ragas.metrics.collections import faithfulness, answer_relevancy


def setup_ragas_llm():
    client = OpenAIClient(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    llm = llm_factory(LLM_MODEL, client=client)
    embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name=BGE_EMBEDDING_MODEL,
            cache_folder=BGE_CACHE_DIR,
            model_kwargs={"device": "cpu"},
        )
    )
    return llm, embeddings


RUNS_DIR = Path("results/runs")


def load_mulchat_records(run_name: str | None = None) -> list[dict]:
    records = []
    for path in sorted(RUNS_DIR.glob("mulchat_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        if run_name is not None and record.get("run_name") != run_name:
            continue
        records.append(record)
    return records


def build_ragas_samples(records: list[dict]) -> Dataset:
    samples = []
    for record in records:
        for turn in record["turns"]:
            sample = {
                "question": turn["standalone_query"],
                "answer": turn["answer"],
                "contexts": turn["retrieved_contexts"],
            }
            samples.append(sample)
    dataset = Dataset.from_list(samples)
    return dataset


def main():
    all_records = load_mulchat_records()
    run_names = list(dict.fromkeys(r["run_name"] for r in all_records))

    if not run_names:
        print("没有找到任何实验记录。")
        return

    print("可用的实验：")
    for i, name in enumerate(run_names):
        print(f"  [{i}] {name}")

    choice = input("请输入编号：").strip()

    try:
        index = int(choice)
    except ValueError:
        print("输入无效，请输入数字。")
        return

    if index < 0 or index >= len(run_names):
        print(f"编号超出范围，请输入 0 到 {len(run_names) - 1} 之间的数字。")
        return

    selected = run_names[index]
    records = load_mulchat_records(run_name=selected)
    samples = build_ragas_samples(records)

    print(f"\n已选择：{selected}")
    print(f"共 {len(samples)} 条样本")

    if len(samples) > 0:
        llm, embeddings = setup_ragas_llm()
        result = evaluate(
            dataset=samples,
            metrics=[faithfulness, answer_relevancy],
            llm=llm,
            embeddings=embeddings,
        )
        print(result)
    else:
        print("没有找到样本数据")

>>>>>>> 3a83f6b (Add multichat RAG, Ragas eval scaffold, and DeepSeek config)

if __name__ == "__main__":
    main()
