from src.indexing.build_index import build_index
from src.indexing.retriever import get_retriever, retrieve, get_contexts,get_sources
from src.llm import setup_llm
from src.rag.generation import generate_answer_with_history, rewrite_query_with_history

from src.rag.trace import save_turn_result


def chat():
    client = setup_llm()
    index = build_index()
    retriever = get_retriever(index)
    history: list[dict[str,str]] = []
    run_name = "deepseek_test1"
    turn = 1


    print("Multi-turn RAG chat started. Type 'exit' to quit.")

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
                f"[{i}] {source['file_name']}, "    #文件名
                f"page {source['page_label']}, "    #页码
                f"score={source['score']:.4f}"      #相似度分数
            )
        answer = generate_answer_with_history(client,query, contexts, history)

        print(f"\nAssistant: {answer}")
        output_path = save_turn_result(
            run_name = input("Run name: ").strip() or "default",
            turn=turn,
            user_input=query,
            standalone_query=standalone_query,
            contexts=contexts,
            sources=sources,
            answer=answer,
        )
        print(f"\nSaved turn result to {output_path}")


        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        turn += 1



if __name__ == "__main__":
    chat()