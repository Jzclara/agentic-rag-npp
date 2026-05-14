# Agentic RAG NPP

一个面向核电厂故障诊断论文语料的 Agentic RAG 学习项目。

当前阶段先实现 LlamaIndex baseline RAG：

1. 从 `data/raw/` 加载 PDF 文档。
2. 使用 `SentenceSplitter` 做基础文本分块。
3. 使用本地 `BAAI/bge-small-en-v1.5` 生成 embedding。
4. 构建并持久化向量索引到 `index/`。
5. 检索相关上下文后，调用 OpenAI-compatible LLM 生成回答。

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

本地已经生成 `.env`。把 Gemini API key 填到 `LLM_API_KEY=` 后即可测试。真实 `.env` 不要提交到 Git。

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=你的 Gemini API key
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.5-flash-lite
```

## Local Embedding

项目默认使用本地 BGE embedding：

```env
BGE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
BGE_CACHE_DIR=.cache/llamaindex
BGE_LOCAL_FILES_ONLY=true
```

首次运行前，需要确保模型已经下载到 `BGE_CACHE_DIR` 对应的缓存目录。本项目当前已下载到 `.cache/llamaindex`。

## Run

```powershell
.venv\Scripts\python.exe -m src.rag.baseline
```

注意：运行前需要先把 PDF 论文放到 `data/raw/`，并在 `.env` 中填写 `LLM_API_KEY`。
