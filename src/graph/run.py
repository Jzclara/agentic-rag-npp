"""
Agentic RAG 单次测试入口。
用一个问题跑一遍完整的图流程，验证所有节点能正常工作。
"""

from src.graph.app import build_graph


def main():
    # 编译图
    graph = build_graph()

    # 构造初始 state
    state = {
        "question": "What is the comparison between CNN and reinforcement learning for severe accident management?",
        "history": [],
        "standalone_query": "",
        "contexts": [],
        "context_sufficient": False,
        "retry_count": 0,
        "max_retries": 2,
        "answer": "",
    }

    print("开始执行 Agentic RAG...\n")
    result = graph.invoke(state)

    print(f"\n最终回答：{result['answer']}")
    print(f"重试次数：{result['retry_count']}")


if __name__ == "__main__":
    main()