from pathlib import Path

from llama_index.core import Document
from pypdf import PdfReader

def load_documents(data_dir: str = "data/raw") -> list:
    # 显式使用 pypdf 按页抽取，避免默认 PDF reader 在部分论文上产生异常重复文本。
    # 每页生成一个 Document，metadata 保留文件名和页码，后续引用来源更方便。
    documents = []
    for pdf_path in sorted(Path(data_dir).glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                continue
            documents.append(
                Document(
                    text=text,
                    metadata={
                        "file_path": str(pdf_path),
                        "file_name": pdf_path.name,
                        "page_label": page_number,
                    },
                )
            )

    print(f"Loaded {len(documents)} PDF pages from {data_dir}")
    return documents
