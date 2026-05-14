from src.indexing.build_index import build_index
from src.indexing.retriever import get_retriever, retrieve, get_contexts
from src.llm import setup_llm
from src.rag.generation import generate_answer_with_history

def chat():
    client = setup_llm()
    index = build_index()
    retriever = get_retriever(index)
    history: list[dict[str, str]] = []

    print("RAG chat started. Type 'exit' to quit.")

    while True:
        query = input("\nYou:").strip()

        if query.lower() in {"exit", "quit"}:
            break

        nodes = retrieve(retriever, query)
        contexts = get_contexts(nodes)
        answer = generate_answer_with_history(client, query, contexts, history)

        print(f"\nAssistant: {answer}")
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    chat()
