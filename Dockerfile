# ─────────────────────────────────────────────────────────────
# 后端镜像：FastAPI + LangGraph + 本地 RAG 检索
# 构建：docker build -t agentic-rag-api .
# ─────────────────────────────────────────────────────────────

# 1. 基础镜像：官方 Python 3.11 精简版（slim，去掉用不到的系统工具）
FROM python:3.11-slim

# 2. 容器内的工作目录。之后所有相对路径都基于 /app。
WORKDIR /app

# 3. 两个环境变量，Python 容器里的标准设置：
#    PYTHONDONTWRITEBYTECODE=1  不生成 .pyc 缓存文件，保持镜像干净
#    PYTHONUNBUFFERED=1         日志实时输出，不被缓冲（docker logs 能立刻看到）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4. 【层缓存关键】先只拷依赖清单，再装依赖。
#    只要 requirements.txt 没变，下面这层 pip install 就一直命中缓存，
#    改代码不会触发漫长的重新安装。
COPY requirements.txt .

# 5a. 【关键优化】先单独装 CPU 版 PyTorch。
#     容器里没有 GPU，默认源会拉好几 G 的 CUDA 库（triton/nvidia_*），纯浪费。
#     这里指定 PyTorch 官方的 CPU 专用源，只装 CPU 版，体积小、下载快。
#     先装好它，下一步 requirements 里依赖 torch 的包就会直接复用，不再拉 GPU 版。
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 5b. 再装项目其余依赖（torch 已满足，不会重复下载）+ uvicorn（线上跑服务用）
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "uvicorn[standard]"

# 6. 依赖装完后，再拷项目代码（这一步快，改代码只重跑这层）
COPY src/ ./src/

# 7. 声明服务端口（文档作用 + 给 compose 提示，真正映射在 run/compose 里做）
EXPOSE 8000

# 8. 容器启动命令。
#    注意 --host 0.0.0.0：容器里必须绑 0.0.0.0，外部才连得进来
#    （绑默认的 127.0.0.1 的话，只有容器内部能访问，外面打不通）
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
