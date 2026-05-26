import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 开发时把 /api 转发到你本地的 FastAPI 后端
    // 这样前端代码里直接 fetch('/api/chat') 即可，无需写完整 URL
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    // 生产构建后，把 dist/ 拷到你的 FastAPI 工程的 static/ 目录即可
    // 或者用 FastAPI 的 StaticFiles 直接挂载 dist/
  },
});
