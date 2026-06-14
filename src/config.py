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

# 通用 OpenAI-compatible LLM 配置。
# 推荐新配置使用 LLM_*；旧的 ZHIPU_* / OPENAI_* 变量仍保留，避免已有 .env 失效。
# LLM 配置（通过 .env 设置，当前使用 DeepSeek）
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")

LLAMA_INDEX_CACHE_DIR = resolve_project_path(
    os.getenv("LLAMA_INDEX_CACHE_DIR", ".cache/llamaindex")
)

# 本地 BGE embedding 配置
# 默认使用项目内缓存，避免依赖某台电脑上的全局 Hugging Face 缓存结构。
BGE_EMBEDDING_MODEL = os.getenv("BGE_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
BGE_CACHE_DIR = resolve_project_path(os.getenv("BGE_CACHE_DIR", LLAMA_INDEX_CACHE_DIR))
BGE_LOCAL_FILES_ONLY = os.getenv("BGE_LOCAL_FILES_ONLY", "true").lower() in {"1", "true", "yes", "y"}

# Reranker 配置
# 粗召回阶段取 top-k 个候选，rerank 后只保留 top-n 个最终结果
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "5"))
RETRIEVER_COARSE_TOP_K = int(os.getenv("RETRIEVER_COARSE_TOP_K", "10"))

# Parent-Child Chunk 配置
# parent 大块用于提供完整上下文，child 小块用于精准检索匹配
PARENT_CHUNK_SIZE = int(os.getenv("PARENT_CHUNK_SIZE", "1024"))
PARENT_CHUNK_OVERLAP = int(os.getenv("PARENT_CHUNK_OVERLAP", "100"))
CHILD_CHUNK_SIZE = int(os.getenv("CHILD_CHUNK_SIZE", "256"))
CHILD_CHUNK_OVERLAP = int(os.getenv("CHILD_CHUNK_OVERLAP", "50"))

# Hybrid Search（混合检索）配置
# BM25 关键词检索的候选数量，和向量检索的 RETRIEVER_COARSE_TOP_K 分别控制两路召回量
BM25_TOP_K = int(os.getenv("BM25_TOP_K", "10"))
# RRF 合并公式中的常数 k，用于压平排名差距，通常取 60
RRF_K = int(os.getenv("RRF_K", "60"))

# Redis 缓存配置（阶段 ③）
# 容器里连服务名 redis，本地默认连 localhost。CACHE_TTL 为答案缓存过期秒数（默认 1 小时）。
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
