from pathlib import Path

from llama_index.core import Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.config import BGE_CACHE_DIR, BGE_EMBEDDING_MODEL, BGE_LOCAL_FILES_ONLY
from src.indexing.chunking import get_text_splitter, get_parent_splitter, get_child_splitter
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


# ── Parent-Child 索引 ──
# 和上面的 build_index 独立，使用不同的目录存储，两套索引互不影响。

from llama_index.core import Document

PARENT_CHILD_INDEX_DIR = "index/parent_child"


def build_parent_child_index() -> VectorStoreIndex:
    """构建 parent-child 索引。
    流程：加载文档 → 切 parent 大块 → 每个 parent 再切 child 小块
    → child 的 metadata 里存 parent 完整文本 → 索引建在 child 上。
    检索时命中 child，但可以从 metadata 取出 parent 作为 LLM 上下文。"""
    setup_embedding_model()

    # 如果已有持久化的 parent-child 索引，直接加载
    index_path = Path(PARENT_CHILD_INDEX_DIR)
    if index_path.exists() and any(
        p.suffix != ".gitkeep" and p.name != ".gitkeep" for p in index_path.iterdir()
    ):
        storage_context = StorageContext.from_defaults(persist_dir=PARENT_CHILD_INDEX_DIR)
        index = load_index_from_storage(storage_context)
        print("Loaded existing parent-child index from disk.")
        return index

    # ── 首次构建 ──
    documents = load_documents()

    parent_splitter = get_parent_splitter()
    child_splitter = get_child_splitter()

    # 第一步：把原始文档切成 parent 大块（默认 1024 token）
    parent_nodes = parent_splitter.get_nodes_from_documents(documents)
    print(f"切出 {len(parent_nodes)} 个 parent 块")

    # 第二步：每个 parent 再切成 child 小块（默认 256 token）
    # 并把 parent 的完整文本存进每个 child 的 metadata，建立父子关系
    all_child_nodes = []
    for parent_node in parent_nodes:
        # 把 parent node 包装成临时 Document，才能喂给 child splitter
        parent_doc = Document(
            text=parent_node.text,
            metadata=parent_node.metadata.copy(),
        )
        children = child_splitter.get_nodes_from_documents([parent_doc])
        for child in children:
            child.metadata["parent_text"] = parent_node.text
        all_child_nodes.extend(children)

    print(f"切出 {len(all_child_nodes)} 个 child 块")

    # 第三步：用 child 块建向量索引
    index = VectorStoreIndex(all_child_nodes)
    index.storage_context.persist(persist_dir=PARENT_CHILD_INDEX_DIR)
    print(f"Parent-child index built and saved to {PARENT_CHILD_INDEX_DIR}")
    return index
