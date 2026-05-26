import re
from pathlib import Path

from llama_index.core import Document
from pypdf import PdfReader


def clean_pdf_text(text: str) -> str:
    """清洗 pypdf 提取的原始文本。"""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append('')
            continue
        # 跳过独占一行的纯数字（行号 / 页码）
        if stripped.isdigit():
            continue
        # 跳过独占一行的单个字母或作者上标标注（a, b, c, a,b, b,c,* 等）
        if re.fullmatch(r'[a-z][,*]*(?:\s*,\s*[a-z][,*]*)*\s*[,*]*', stripped):
            continue
        cleaned.append(stripped)

    # 合并被换行打断的句子
    merged = []
    for line in cleaned:
        if not line:
            merged.append('')
            continue
        if (merged
                and merged[-1]
                and not merged[-1][-1] in '.!?:;'
                and not line[0].isupper()
                and not re.match(r'^[\d•\-–—\[]', line)):
            merged[-1] += ' ' + line
        else:
            merged.append(line)

    # 去掉连续空行
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(merged))
    return result.strip()


def load_documents(data_dir: str = "data/raw") -> list:
    documents = []
    for pdf_path in sorted(Path(data_dir).glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = clean_pdf_text(text)
            if not text:
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
