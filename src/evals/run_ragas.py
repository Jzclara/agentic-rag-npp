"""
Ragas 评估脚本，支持两种模式：
  模式 1 (eval_from_records)：读取 results/runs/ 下已有的 mulchat 对话日志，直接评估
  模式 2 (run_testset_eval)：读取 testset.jsonl 固定问题集，自动跑多轮对话后评估
    - 模式 2 的分数可用于不同版本间对比（baseline vs Agentic RAG），因为问题固定
"""

import json
from pathlib import Path
from datetime import datetime

from openai import OpenAI as OpenAIClient
from ragas.llms import llm_factory
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy

from src.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    BGE_EMBEDDING_MODEL,
    BGE_CACHE_DIR,
)
from src.indexing.build_index import build_index
from src.indexing.retriever import get_retriever, retrieve, get_contexts
from src.llm import setup_llm
from src.rag.generation import generate_answer_with_history, rewrite_query_with_history

from src.graph.app import build_graph

# ── 路径常量 ──

RUNS_DIR = Path("results/runs")
TESTSET_PATH = Path(__file__).parent / "testset.jsonl"


# ── Ragas 初始化 ──


def setup_ragas_llm():
    """初始化 Ragas 评估用的 LLM 和 Embedding。
    Ragas 内部用 LLM 判断 faithfulness（答案是否有检索内容支持），
    用 Embedding 计算 answer_relevancy（答案和问题的语义相似度）。"""
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


# ── 通用：保存评估结果 ──


def save_eval_result(result, run_name: str, num_samples: int):
    """把 Ragas 评估分数保存为 JSON 到 results/evals/，方便后续版本对比。"""
    evals_dir = Path("results/evals")
    evals_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": timestamp,
        "run_name": run_name,
        "model": LLM_MODEL,
        "num_samples": num_samples,
        "scores": result.to_pandas()[["faithfulness", "answer_relevancy"]].mean().to_dict(),
    }
    output_path = evals_dir / f"eval_{timestamp}_{run_name}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"评估结果已保存到 {output_path}")


# ── 模式 1：从已有对话记录评估 ──


def load_mulchat_records(run_name: str | None = None) -> list[dict]:
    """扫描 results/runs/ 下所有 mulchat_*.json 日志。
    可选传入 run_name 只读取特定实验的记录。"""
    records = []
    for path in sorted(RUNS_DIR.glob("mulchat_*.json")):
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        if run_name is not None and record.get("run_name") != run_name:
            continue
        records.append(record)
    return records


def build_ragas_samples(records: list[dict]) -> Dataset:
    """把 mulchat 日志转成 Ragas 需要的格式：question / answer / contexts。
    遍历每条记录的每一轮对话，提取这三个字段。"""
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


def eval_from_records():
    """模式 1：从已有对话日志评估。
    适合评估你手动跑过的 mulchat 对话质量。"""
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
            metrics=[Faithfulness(), AnswerRelevancy()],
            llm=llm,
            embeddings=embeddings,
        )
        print(result)
        save_eval_result(result, run_name=selected, num_samples=len(samples))
    else:
        print("没有找到样本数据")


# ── 模式 2：从 testset.jsonl 自动运行评估 ──


def load_testset() -> list[dict]:
    """读取 testset.jsonl，每行是一组多轮对话：
    {"group": "组名", "turns": ["问题1", "问题2", ...]}"""
    groups = []
    with open(TESTSET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            groups.append(json.loads(line))
    return groups


def run_testset_eval():
    """模式 2：从 testset.jsonl 自动运行多轮对话并评估。
    流程：读取固定问题 → 逐组模拟多轮对话（rewrite → 检索 → 生成）→ Ragas 打分 → 保存。
    因为问题固定，每次改进系统后重跑，分数可直接对比。"""
    print("加载模型和索引...")
    client = setup_llm()
    index = build_index()
    retriever = get_retriever(index)

    all_samples = []

    groups = load_testset()
    print(f"共 {len(groups)} 组对话，开始自动运行...\n")

    for group in groups:
        group_name = group["group"]
        turns = group["turns"]
        # 每组对话独立维护历史，模拟真实多轮场景
        history: list[dict[str, str]] = []

        print(f"--- {group_name} ---")

        for question in turns:
            # 1. 用对话历史改写问题，解析指代词（如 "they" → 具体方法名）
            standalone_query = rewrite_query_with_history(client, question, history)
            # 2. 用改写后的问题检索相关文档片段
            nodes = retrieve(retriever, standalone_query)
            contexts = get_contexts(nodes)
            # 3. 基于检索上下文和对话历史生成回答
            answer = generate_answer_with_history(client, question, contexts, history)

            print(f"  Q: {question}")
            print(f"  A: {answer[:100]}...")

            # 收集 Ragas 需要的三元组：改写后的问题、回答、检索上下文
            all_samples.append({
                "question": standalone_query,
                "answer": answer,
                "contexts": contexts,
            })

            # 更新对话历史，供下一轮 rewrite 和生成使用
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})

        print()

    print(f"共 {len(all_samples)} 条样本，开始评估...\n")

    dataset = Dataset.from_list(all_samples)
    llm, embeddings = setup_ragas_llm()
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy()],
        llm=llm,
        embeddings=embeddings,
    )
    print(result)
    save_eval_result(result, run_name="testset_baseline", num_samples=len(all_samples))


# ── 模式 3：用 Agentic RAG 图跑 testset 评估 ──

def run_testset_agentic_eval():
    """模式 3：用 LangGraph Agentic RAG 图跑 testset.jsonl 并评估。
    和模式 2 的区别：模式 2 是线性的 rewrite → retrieve → generate，
    模式 3 走完整的图流程，包含 grade 判断、重试和 fallback。"""
    print("编译 Agentic RAG 图...")
    graph = build_graph()

    all_samples = []

    groups = load_testset()
    print(f"共 {len(groups)} 组对话，开始自动运行...\n")

    for group in groups:
        group_name = group["group"]
        turns = group["turns"]
        # 每组对话独立维护历史
        history: list[dict[str, str]] = []

        print(f"--- {group_name} ---")

        for question in turns:
            # 构造初始 state，交给图去执行
            state = {
                "question": question,
                "history": history,
                "standalone_query": "",
                "contexts": [],
                "context_sufficient": False,
                "retry_count": 0,
                "max_retries": 2,
                "answer": "",
            }

            # 图自动执行所有节点（rewrite → retrieve → grade → generate/fallback）
            result = graph.invoke(state)

            print(f"  Q: {question}")
            print(f"  A: {result['answer'][:100]}...")
            print(f"  重试: {result['retry_count']} 次")

            all_samples.append({
                "question": result["standalone_query"],
                "answer": result["answer"],
                "contexts": result["contexts"],
            })

            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": result["answer"]})

        print()

    print(f"共 {len(all_samples)} 条样本，开始评估...\n")

    dataset = Dataset.from_list(all_samples)
    llm, embeddings = setup_ragas_llm()
    eval_result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy()],
        llm=llm,
        embeddings=embeddings,
    )
    print(eval_result)
    save_eval_result(eval_result, run_name="testset_agentic", num_samples=len(all_samples))


# ── 入口 ──


def main():
    print("选择评估模式：")
    print("  [1] 从已有对话记录评估")
    print("  [2] 从 testset.jsonl 自动运行评估（标准化，可对比）")
    print("  [3] 从 testset.jsonl 自动运行评估（Agentic RAG）")
    choice = input("请输入编号：").strip()

    if choice == "1":
        eval_from_records()
    elif choice == "2":
        run_testset_eval()
    elif choice == "3":
        run_testset_agentic_eval()    
    else:
        print("输入无效。")


if __name__ == "__main__":
    main()
