from openai import OpenAI

from src.config import LLM_MODEL
from src.memory import format_history


def generate_answer(client: OpenAI, query: str, contexts: list[str]) -> str:
    context_str = "\n\n".join(contexts)
    prompt = (
        f"Answer the question based only on the context below.\n\n"
        f"Context:\n{context_str}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You answer questions using only the provided retrieval context.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def generate_answer_with_history(
    client: OpenAI,
    query: str,
    contexts: list[str],
    history: list[dict[str, str]],
) -> str:
    context_str = "\n\n".join(contexts)
    history_str = format_history(history)
    prompt = (
        "Answer the current question based only on the retrieved context below.\n"
        "Use the conversation history only to understand what the user is referring to.\n"
        "If the retrieved context does not contain enough evidence, say you do not know.\n\n"
        f"Conversation history:\n{history_str}\n\n"
        f"Retrieved context:\n{context_str}\n\n"
        f"Current question:\n{query}\n\n"
        "Answer:"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a RAG assistant. Answer using only the retrieved paper context.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""

def rewrite_query_with_history(
        client: OpenAI,
        query: str,
        history: list[dict[str,str]],

)->str:
    history_str = format_history(history)
    prompt = (
    "Rewrite the current user question into one clear standalone search query for document retrieval.\n"
    "Use the conversation history only to resolve references such as 'it', 'they', 'these methods', or 'their'.\n"
    "Do not answer the question.\n"
    "Do not add explanations.\n"
    "Return only the rewritten search query.\n"
    "If the current question is already standalone, return it unchanged.\n\n"
    f"Conversation history:\n{history_str}\n\n"
    f"Current question:\n{query}\n\n"
    "Standalone search query:"
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You rewrite conversational questions into standalone retrieval queries.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or query
