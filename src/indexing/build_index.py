from pathlib import Path

from llama_index.core import Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.config import BGE_CACHE_DIR, BGE_EMBEDDING_MODEL, BGE_LOCAL_FILES_ONLY
from src.indexing.chunking import get_text_splitter
from src.indexing.loaders import load_documents

# 向量索引的持久化目录。
# 只要这里已经有可用索引，就优先加载，避免每次都重复做 embedding。
INDEX_DIR = "index"


def setup_embedding_model() -> None:
    # 本地 BGE embedding 配置：
    # 1. model_name 指向 BAAI/bge-small-en-v1.5
    # 2. cache_folder 指向本地 Hugging Face 缓存目录
    # 3. local_files_only=True 时只允许读本地文件，禁止联网补下载
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=BGE_EMBEDDING_MODEL,
        cache_folder=BGE_CACHE_DIR,
        local_files_only=BGE_LOCAL_FILES_ONLY,
    )


def build_index() -> VectorStoreIndex:
    setup_embedding_model()

    # 这里使用句子级切分器作为第一阶段的基础 chunk 策略。
    text_splitter = get_text_splitter()
    Settings.text_splitter = text_splitter

    # 如果 index 目录里已经有持久化索引，就直接加载。
    index_path = Path(INDEX_DIR)
    if index_path.exists() and any(
        p.suffix != ".gitkeep" and p.name != ".gitkeep" for p in index_path.iterdir()
    ):
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        index = load_index_from_storage(storage_context)
        print("Loaded existing index from disk.")
        return index

    # 首次运行时，加载原始文档并构建向量索引。
    documents = load_documents()
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=[text_splitter],
    )
    index.storage_context.persist(persist_dir=INDEX_DIR)
    print(f"Index built and saved to {INDEX_DIR}")
    return index
