from openai import OpenAI

from src.config import LLM_API_KEY, LLM_BASE_URL


def setup_llm() -> OpenAI:
    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not set. Fill it in .env before running RAG.")

    return OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )
