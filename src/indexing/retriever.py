from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

def get_retriever(index: VectorStoreIndex, top_k: int = 5):
    # as_retriever 把索引包装成检索器，检索时返回相似度最高的 top_k 个 chunk
    return index.as_retriever(similarity_top_k=top_k)

def retrieve(retriever, query: str) -> list[NodeWithScore]:
    # 每个 NodeWithScore 包含 node.text（chunk 文本）和 score（相似度分数）
    nodes = retriever.retrieve(query)
    return nodes

def get_contexts(nodes: list[NodeWithScore]) -> list[str]:
    # 把 NodeWithScore 列表转成纯文本列表，方便传给 LLM 和 Ragas 评估
    return [node.node.text for node in nodes]