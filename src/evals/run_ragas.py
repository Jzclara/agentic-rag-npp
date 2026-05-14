import json
from pathlib import Path

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

if __name__ == "__main__":
    main()
