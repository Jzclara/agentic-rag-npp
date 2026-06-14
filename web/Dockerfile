# ─────────────────────────────────────────────────────────────
# 前端镜像：多阶段构建
#   阶段 1（builder）：用 Node 把 React 代码打包成静态文件 dist/
#   阶段 2（runtime）：用 Nginx 托管 dist/，并把 /api 转发给后端
# 构建（在 web/ 目录下）：docker build -t agentic-rag-web .
# ─────────────────────────────────────────────────────────────

# ===== 阶段 1：构建静态文件 =====
# 给这一段起名叫 builder，下一段会用 --from=builder 取它的产物
FROM node:20-alpine AS builder

WORKDIR /app

# 【层缓存】先只拷依赖清单，装依赖。清单没变就一直命中缓存。
COPY package.json package-lock.json ./
RUN npm ci

# 再拷前端源码，执行打包，产出 /app/dist
COPY . .
RUN npm run build

# ===== 阶段 2：用 Nginx 托管 =====
# 换成极小的 Nginx 镜像，前面那套 Node 环境全部丢掉
FROM nginx:alpine

# 把阶段 1 打包好的 dist/ 拷到 Nginx 的默认网站根目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 用我们自己的 Nginx 配置覆盖默认配置（托管 + 转发 /api）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Nginx 默认监听 80 端口
EXPOSE 80

# 前台运行 Nginx（容器里服务都要前台跑，否则容器会立刻退出）
CMD ["nginx", "-g", "daemon off;"]
