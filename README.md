# Agentic RAG NPP

面向核电厂故障诊断论文语料的 **Agentic RAG 全栈应用**：前端对话界面 + FastAPI/LangGraph 后端 + 关系数据库持久化 + 缓存，全部由 `docker-compose` 一键启动。

> 从「能在本机跑的 RAG 脚本」逐步工程化为「具备前端 + Agent 编排 + 数据库 + 缓存 + 容器化部署的完整项目」。详见 [docs/工程化迭代路线.md](docs/工程化迭代路线.md)。

## 架构

```
              浏览器
                │
                ▼
        ┌───────────────┐
        │  web (Nginx)  │  托管前端 + 反向代理 /api（支持 SSE 流式）
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │  api (FastAPI)│  RAG 检索 + LangGraph Agent 编排
        └───┬───────┬───┘
            │       │
      ┌─────▼──┐ ┌──▼─────┐
      │  db    │ │ redis  │  PostgreSQL 持久化 + Redis 缓存
      │ (PG)   │ │        │
      └────────┘ └────────┘
```

## 核心特性

- **Agentic 编排（LangGraph）**：`改写 → 检索 → 质量评分 → 生成 → 兜底`，检索不足时自动重试。
- **混合检索 + 重排**：向量召回 + BM25 关键词召回 → RRF 融合 → cross-encoder 重排，兼顾语义与精确术语。
- **Parent-Child 分块**：child 小块精准匹配、parent 大块提供完整上下文。
- **流式问答（SSE）**：逐节点推送执行轨迹，前端实时展示进度与引用来源。
- **实时评估（Ragas）**：每次回答即时给出 faithfulness / answer_relevancy 分数。
- **PDF 来源溯源**：答案引用可定位到原文 PDF 页面并高亮。
- **聊天记录持久化（PostgreSQL）**：关系字段 + JSONB 混合建模，富结构零丢失。
- **答案缓存（Redis）**：独立问题命中缓存秒级返回、零 LLM 调用，连接失败自动降级。

## 工程化阶段

| 阶段 | 内容 | 状态 |
|---|---|---|
| ① Docker 化 | 后端/前端镜像 + 多阶段构建 + Nginx 反代 + compose 编排 | ✅ |
| ② PostgreSQL 持久化 | 关系建模 + 连接池 + 事务 + 数据迁移脚本 | ✅ |
| ③ Redis 缓存 | 答案缓存 + TTL + 优雅降级 + 前端「⚡ 缓存命中」 | ✅ |

## 快速开始（Docker，推荐）

**前置**：安装 Docker Desktop。

1. **配置 `.env`**（项目根目录，不会提交到 Git）：

   ```env
   LLM_PROVIDER=openai-compatible
   LLM_API_KEY=你的 API key
   LLM_BASE_URL=https://api.deepseek.com
   LLM_MODEL=deepseek-chat
   ```

2. **放入论文 PDF**：把文献放到 `data/raw/`（该目录已被 Git 忽略，首次运行会自动构建索引到 `index/`）。

3. **一键启动**：

   ```bash
   docker compose up --build        # 加 -d 后台运行
   ```

   - 前端：http://localhost:8080
   - 后端 API：http://localhost:8000
   - 首次启动较慢（构建镜像 + 加载/下载模型），之后启动很快。

   常用命令：

   ```bash
   docker compose ps          # 查看四个容器状态
   docker compose logs -f api # 实时查看后端日志
   docker compose down        # 停止（数据卷保留）
   docker compose down -v     # 停止并清空数据卷
   ```

## 本地开发（不走 Docker）

后端依赖 PostgreSQL 和 Redis，最省事是用容器只起这两个依赖，应用本机跑：

```powershell
# 1) 起依赖
docker compose up -d db redis

# 2) 后端（.env 里把连接串指向 localhost）
#    DATABASE_URL=postgresql://rag:rag_pwd@localhost:5432/ragdb
#    REDIS_URL=redis://localhost:6379/0
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\uvicorn.exe src.server:app --reload --port 8000

# 3) 前端
cd web
npm install
npm run dev
```

## 评估（Ragas）

Ragas 评估读取 `results/runs/` 的运行记录，结果写入 `results/evals/`：

```powershell
.venv\Scripts\python.exe -m src.evals.run_ragas              # 交互式选择
.venv\Scripts\python.exe -m src.evals.run_ragas --run-name Mulchat1
```

## 目录结构

```
src/
  server.py          FastAPI 服务（SSE 流式 /api/chat、聊天记录接口）
  graph/             LangGraph Agent：节点与编排（rewrite/retrieve/grade/generate/fallback）
  indexing/          索引构建、加载、混合检索与重排
  rag/               baseline / 生成 / 多轮对话
  evals/             Ragas 评估
  db.py              PostgreSQL 持久化层
  cache.py           Redis 缓存层
web/                 前端（Vite + React）+ Nginx 配置
scripts/             迁移等辅助脚本
docs/                工程化路线、项目计划、学习笔记
docker-compose.yml   web / api / db / redis 一键编排
```

## 注意事项

- `index/`、`data/`、`.cache/`、`results/`、`.env` 均已被 Git 忽略，不进版本库。
- 克隆后首次运行：在 `data/raw/` 放入 PDF，应用启动时会自动构建索引（若 `index/` 为空）。
- 改了 `src/` 代码需 `docker compose up --build` 重建镜像；只改挂载数据（index/data/cache）重启容器即可。
