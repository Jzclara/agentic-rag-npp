from src.indexing.build_index import build_index
from src.indexing.retriever import get_retriever, retrieve, get_contexts, get_sources
from src.llm import setup_llm
from src.rag.generation import generate_answer_with_history, rewrite_query_with_history
from src.rag.trace import save_session


def chat():
    print("Starting multi-turn RAG chat...", flush=True)

    print("Setting up LLM client...", flush=True)
    client = setup_llm()
    print("LLM client ready.", flush=True)

    print("Loading index. This may take 1-2 minutes...", flush=True)
    index = build_index()
    print("Index ready.", flush=True)

    print("Creating retriever...", flush=True)
    retriever = get_retriever(index)
    print("Retriever ready.", flush=True)

    history: list[dict[str, str]] = []
    turns: list[dict] = []
    turn = 1

    print("Multi-turn RAG chat started. Type 'exit' to quit.", flush=True)

    while True:
        query = input("\nYou: ").strip()

        if query.lower() in {"exit", "quit"}:
            break

        standalone_query = rewrite_query_with_history(client, query, history)
        print(f"\nSearch query: {standalone_query}")

        nodes = retrieve(retriever, standalone_query)
        contexts = get_contexts(nodes)
        sources = get_sources(nodes)
        print("\nSources:")
        for i, source in enumerate(sources, start=1):
            print(
                f"[{i}] {source['file_name']}, "
                f"page {source['page_label']}, "
                f"score={source['score']:.4f}"
            )

        answer = generate_answer_with_history(client, query, contexts, history)
        print(f"\nAssistant: {answer}")

        turns.append({
            "turn": turn,
            "user_input": query,
            "standalone_query": standalone_query,
            "sources": sources,
            "retrieved_contexts": contexts,
            "answer": answer,
        })

        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        turn += 1

    # 对话结束后统一保存
    if turns:
        run_name = input("\n本次对话的名称（直接回车用 default）: ").strip() or "default"
        output_path = save_session(run_name=run_name, turns=turns)
        print(f"已保存到 {output_path}")


if __name__ == "__main__":
    chat()
