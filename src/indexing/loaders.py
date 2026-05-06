from pathlib import Path
from llama_index.core import SimpleDirectoryReader

def load_documents(data_dir: str = "data/raw") -> list:
    # SimpleDirectoryReader 扫描目录，把 PDF 提取成 Document 对象列表
    # 每个 Document 包含 text（文本内容）和 metadata（文件名、页码等）
    documents = SimpleDirectoryReader(
        input_dir=data_dir,
        required_exts=[".pdf"],  # 只加载 PDF，过滤掉 .gitkeep 等无关文件
        recursive=False,         # 不递归进入子目录
    ).load_data()
    print(f"Loaded {len(documents)} document chunks from {data_dir}")
    return documents
