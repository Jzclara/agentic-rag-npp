"""
一键运行 4 组对比评估（2 检索策略 × 2 管线类型），输出对比表格。

使用方式：
  .venv\Scripts\python.exe -m src.evals.run_comparison
"""

import json
import time
from pathlib import Path
from datetime import datetime

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy

from src.evals.run_ragas import (
    setup_ragas_llm, load_testset,
    TESTSET_PATH, TESTSET2_PATH,
)
from src.indexing.build_index import build_index
from src.indexing.retriever import (
    get_retriever, retrieve, get_contexts,
    rerank_nodes, setup_bm25, hybrid_retrieve,
)
from src.llm import setup_llm
from src.rag.generation import generate_answer_with_history, rewrite_query_with_history
from src.graph.app import build_graph


# ── 运行单组评估 ──

def run_baseline(client, retriever, index, groups, use_hybrid: bool) -> list[dict]:
    """跑 Baseline 线性管线（rewrite → retrieve → generate），返回 Ragas 样本列表。"""
    all_samples = []
    for group in groups:
        history: list[dict[str, str]] = []
        for question in group["turns"]:
            standalone_query = rewrite_query_with_history(client, question, history)

            if use_hybrid:
                fused = hybrid_retrieve(standalone_query, retriever)
                ranked = rerank_nodes(standalone_query, fused)
            else:
                raw = retrieve(retriever, standalone_query)
                ranked = rerank_nodes(standalone_query, raw)

            contexts = get_contexts(ranked)
            answer = generate_answer_with_history(client, question, contexts, history)

            all_samples.append({
                "question": standalone_query,
                "answer": answer,
                "contexts": contexts,
            })
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
    return all_samples


def run_agentic(groups, retriever_type: str) -> list[dict]:
    """跑 Agentic 图管线（rewrite → retrieve → grade → generate/fallback），返回 Ragas 样本列表。"""
    graph = build_graph(retriever_type=retriever_type)
    all_samples = []
    for group in groups:
        history: list[dict[str, str]] = []
        for question in group["turns"]:
            state = {
                "question": question,
                "history": history,
                "standalone_query": "",
                "contexts": [],
                "sources": [],
                "context_sufficient": False,
                "retry_count": 0,
                "max_retries": 2,
                "answer": "",
            }
            result = graph.invoke(state)

            all_samples.append({
                "question": result["standalone_query"],
                "answer": result["answer"],
                "contexts": result["contexts"],
            })
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": result["answer"]})
    return all_samples


def ragas_eval(samples: list[dict], llm, embeddings) -> dict:
    """对一组样本跑 Ragas 评估，返回 {faithfulness, answer_relevancy}。"""
    dataset = Dataset.from_list(samples)
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy()],
        llm=llm,
        embeddings=embeddings,
    )
    scores = result.to_pandas()[["faithfulness", "answer_relevancy"]].mean().to_dict()
    return scores


# ── 输出表格 ──

def print_table(results: dict, num_samples: int):
    """打印对比表格。"""
    print()
    print("=" * 70)
    print(f"  对比评估结果（每组 {num_samples} 题）")
    print("=" * 70)
    print()
    print(f"  {'组合':<28} {'Faithfulness':>14} {'Relevancy':>14}")
    print(f"  {'-'*28} {'-'*14} {'-'*14}")

    for name, scores in results.items():
        f = scores["faithfulness"]
        r = scores["answer_relevancy"]
        f_str = f"{f:.4f}" if f == f else "N/A"  # NaN check
        r_str = f"{r:.4f}" if r == r else "N/A"
        print(f"  {name:<28} {f_str:>14} {r_str:>14}")

    print()

    # 差异分析
    keys = list(results.keys())
    if len(keys) == 4:
        vb = results[keys[0]]  # vector_baseline
        va = results[keys[1]]  # vector_agentic
        hb = results[keys[2]]  # hybrid_baseline
        ha = results[keys[3]]  # hybrid_agentic

        print("  ── 差异分析 ──")
        print()
        print(f"  {'对比项':<32} {'Faithfulness':>14} {'Relevancy':>14}")
        print(f"  {'-'*32} {'-'*14} {'-'*14}")

        def diff_str(a, b):
            if a != a or b != b:
                return "N/A"
            d = a - b
            return f"{d:+.4f}"

        print(f"  {'Agent 效果（纯向量）':<28} "
              f"{diff_str(va['faithfulness'], vb['faithfulness']):>14} "
              f"{diff_str(va['answer_relevancy'], vb['answer_relevancy']):>14}")

        print(f"  {'Agent 效果（Hybrid）':<28} "
              f"{diff_str(ha['faithfulness'], hb['faithfulness']):>14} "
              f"{diff_str(ha['answer_relevancy'], hb['answer_relevancy']):>14}")

        print(f"  {'Hybrid 效果（Baseline）':<28} "
              f"{diff_str(hb['faithfulness'], vb['faithfulness']):>14} "
              f"{diff_str(hb['answer_relevancy'], vb['answer_relevancy']):>14}")

        print(f"  {'Hybrid 效果（Agentic）':<28} "
              f"{diff_str(ha['faithfulness'], va['faithfulness']):>14} "
              f"{diff_str(ha['answer_relevancy'], va['answer_relevancy']):>14}")

        print()

    print("=" * 70)


def save_comparison(results: dict, num_samples: int, testset_name: str):
    """保存完整对比结果到 JSON。"""
    evals_dir = Path("results/evals")
    evals_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": timestamp,
        "testset": testset_name,
        "num_samples": num_samples,
        "results": results,
    }
    path = evals_dir / f"comparison_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  对比结果已保存到 {path}")


# ── 入口 ──

def main():
    print("=" * 50)
    print("  一键对比评估（4 组：2 检索 × 2 管线）")
    print("=" * 50)
    print()

    # 选择测试集
    print("选择测试集：")
    print("  [1] testset.jsonl  — 2 组 8 题（快速，约 10 分钟）")
    print("  [2] testset2.jsonl — 8 组 32 题（完整，约 40 分钟）")
    choice = input("请输入编号（默认 1）：").strip()

    if choice == "2":
        testset_path = TESTSET2_PATH
        testset_name = "testset2（8 组 32 题）"
    else:
        testset_path = TESTSET_PATH
        testset_name = "testset（2 组 8 题）"

    groups = load_testset(testset_path)
    num_samples = sum(len(g["turns"]) for g in groups)
    print(f"\n已选择：{testset_name}，共 {num_samples} 题")
    print()

    # 初始化公共组件
    print("[0/4] 初始化模型和索引...")
    client = setup_llm()
    index = build_index()
    retriever = get_retriever(index)
    setup_bm25(index)
    llm, embeddings = setup_ragas_llm()
    print()

    results = {}
    total_start = time.time()

    # ── ① 纯向量 + Baseline ──
    print("[1/4] 纯向量 + Baseline ...")
    t0 = time.time()
    samples = run_baseline(client, retriever, index, groups, use_hybrid=False)
    scores = ragas_eval(samples, llm, embeddings)
    results["① 纯向量 Baseline"] = scores
    print(f"      完成，耗时 {int(time.time()-t0)}s，faithfulness={scores['faithfulness']:.4f}")
    print()

    # ── ② 纯向量 + Agentic ──
    print("[2/4] 纯向量 + Agentic ...")
    t0 = time.time()
    samples = run_agentic(groups, retriever_type="vector")
    scores = ragas_eval(samples, llm, embeddings)
    results["② 纯向量 Agentic"] = scores
    print(f"      完成，耗时 {int(time.time()-t0)}s，faithfulness={scores['faithfulness']:.4f}")
    print()

    # ── ③ Hybrid + Baseline ──
    print("[3/4] Hybrid + Baseline ...")
    t0 = time.time()
    samples = run_baseline(client, retriever, index, groups, use_hybrid=True)
    scores = ragas_eval(samples, llm, embeddings)
    results["③ Hybrid Baseline"] = scores
    print(f"      完成，耗时 {int(time.time()-t0)}s，faithfulness={scores['faithfulness']:.4f}")
    print()

    # ── ④ Hybrid + Agentic ──
    print("[4/4] Hybrid + Agentic ...")
    t0 = time.time()
    samples = run_agentic(groups, retriever_type="hybrid")
    scores = ragas_eval(samples, llm, embeddings)
    results["④ Hybrid Agentic"] = scores
    print(f"      完成，耗时 {int(time.time()-t0)}s，faithfulness={scores['faithfulness']:.4f}")
    print()

    total_min = (time.time() - total_start) / 60
    print(f"全部完成，总耗时 {total_min:.1f} 分钟")

    # 输出表格 + 保存
    print_table(results, num_samples)
    save_comparison(results, num_samples, testset_name)


if __name__ == "__main__":
    main()
