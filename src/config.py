import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(path_value: str) -> str:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return str(path)
    return str(PROJECT_ROOT / path)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai-compatible")

# 旧的 provider 配置，已不再使用，保留仅供参考
# ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
# ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL")
# ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash")
# ZHIPU_EMBEDDING_MODEL = os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-3")

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
# OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
# OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# 当前使用 DeepSeek openai-compatible 配置
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")

# 通用 OpenAI-compatible LLM 配置。
# 推荐新配置使用 LLM_*；旧的 ZHIPU_* / OPENAI_* 变量仍保留，避免已有 .env 失效。
LLM_API_KEY = os.getenv("LLM_API_KEY") or ZHIPU_API_KEY or OPENAI_API_KEY
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or ZHIPU_BASE_URL
    or OPENAI_BASE_URL
    or "https://generativelanguage.googleapis.com/v1beta/openai/"
)
LLM_MODEL = os.getenv("LLM_MODEL") or ZHIPU_MODEL or OPENAI_MODEL

LLAMA_INDEX_CACHE_DIR = resolve_project_path(
    os.getenv("LLAMA_INDEX_CACHE_DIR", ".cache/llamaindex")
)

# 本地 BGE embedding 配置
# 默认使用项目内缓存，避免依赖某台电脑上的全局 Hugging Face 缓存结构。
BGE_EMBEDDING_MODEL = os.getenv("BGE_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
BGE_CACHE_DIR = resolve_project_path(os.getenv("BGE_CACHE_DIR", LLAMA_INDEX_CACHE_DIR))
BGE_LOCAL_FILES_ONLY = os.getenv("BGE_LOCAL_FILES_ONLY", "true").lower() in {"1", "true", "yes", "y"}
