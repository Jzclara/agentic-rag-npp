# 论文助读 · 前端工程（Vite + React）

## 快速开始

```bash
cd vite-app
npm install
npm run dev
```

打开 `http://localhost:5173/` 即可看到界面。

## 目录结构

```
vite-app/
├── index.html              Vite 入口（仅 <div id="root"> 和挂载脚本）
├── vite.config.js          含 /api → localhost:8000 的开发代理
├── package.json
└── src/
    ├── main.jsx            React 挂载点
    ├── App.jsx             主应用（顶栏、侧栏、对话区、检视面板的组合）
    ├── styles.css          全部样式（CSS 变量定义在最上方）
    ├── data.js             示例数据 / 兜底默认值
    ├── api.js              后端调用封装（fetchPapers / chatStream / 等等）
    └── components/
        ├── Icons.jsx       全部 SVG 图标
        ├── Sidebar.jsx     左侧文献库 + 最近对话
        ├── Composer.jsx    底部输入框
        ├── Chat.jsx        对话流（用户气泡、助手回答、引用条、思考中）
        ├── Inspector.jsx   右侧三 Tab：推理过程 / 引用来源 / 评估
        └── tweaks/
            └── TweaksPanel.jsx   悬浮 Tweaks 面板 + 各控件
```

## 微调工作流

启动 `npm run dev` 后，**任何 JSX/CSS 改动都会热更新**，不需要刷新页面。改完直接看效果。

常见微调入口：
- 文案 / 占位符 → 对应组件文件
- 颜色 / 字体 / 间距 → `src/styles.css` 顶部的 CSS 变量
- 默认 Tweaks 配置 → `src/App.jsx` 顶部的 `TWEAK_DEFAULTS`
- 示例对话 / 论文列表 / 建议问题 → `src/data.js`

## 接入后端（关键步骤）

UI 目前用 `src/data.js` 的示例数据。要接通真实后端，**只需要改 4 个函数 + 启用 `api.js`**：

### 1. 启动 FastAPI（在 `agentic-rag-npp-workspace/` 那边）

```python
# src/api/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 开发期
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由实现见下文
```

启动：`uvicorn src.api.server:app --reload --port 8000`

### 2. 在 `vite-app/src/api.js` 里，函数已经写好了壳。你只需要：

- 解开 `App.jsx` 启动时的 `await fetchPapers()` 调用注释
- 把 `sendMessage` 里的 mock 改为 `chatStream(...)`
- 把 `addFiles` 改为 `uploadPaper(file)`
- 把 `removePaper` 改为 `deletePaper(id)`

具体接口约定见 `src/api.js` 顶部注释。

### 3. 部署到生产

```bash
npm run build
# 产出 dist/ 目录
```

然后在 FastAPI 里挂载：
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="dist", html=True))
```

这时前端和后端是同一个 origin，CORS 配置可以关掉。

## 与原 Babel-in-Browser 版本的区别

| 旧版（根目录的 `index.html` 等） | Vite 版（本目录） |
|---|---|
| `<script src>` 直接加载，浏览器解析 | 走 `import/export` 模块化 |
| 每次刷新页面才能看效果 | HMR 热更新，改完即看 |
| 全局变量 `window.PAPERS` | 命名导出 `import { PAPERS }` |
| 没有构建 | `npm run build` 产出生产包 |

视觉、交互、组件结构完全一致，只是工程化了。
