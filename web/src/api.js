/* ─────────────────────────────────────────────────────────────
   后端调用封装层
   ─────────────────────────────────────────────────────────────

   接入后端时，App.jsx / Sidebar.jsx 里只需要调下面这几个函数。
   开发期所有 /api/* 请求会被 vite.config.js 的 proxy 转发到
   localhost:8000（即你本地 FastAPI）。

   建议的后端接口约定（你在 FastAPI 那边按这个实现）：

   GET    /api/papers
     → 200 [
         { id, title, short, authors, venue, year, pages, tag, selected }
       ]

   POST   /api/papers/upload   (multipart/form-data, field name = "file")
     → 200 { id, title, short, authors, year, tag, selected: true }

   DELETE /api/papers/{id}
     → 200 { ok: true }

   POST   /api/chat            (Server-Sent Events)
     body: { question, chat_id?, selected_paper_ids?, history? }
     events (每个事件都是 JSON)：
       node_start  { name: "rewrite"|"retrieve"|"grade"|"generate" }
       node_done   { name, ms, detail, verdict?, subnodes?, retry? }
       standalone  { text }                              // 改写后的 query
       answer      { parts: [...], sources: [...] }      // 见 data.js 中
                                                         //   message.answer 与
                                                         //   SOURCES_BAYES_Q1 的结构
       done        { totalMs, tokens, retries }
       error       { message }
   ───────────────────────────────────────────────────────────── */

const BASE = '/api';

/* 当后端没启动时，所有调用都会 reject —— App.jsx 里会 catch 后回退到示例数据 */

export async function fetchEvals() {
  const r = await fetch(`${BASE}/evals`);
  if (!r.ok) throw new Error(`fetchEvals ${r.status}`);
  return r.json();
}

export async function fetchConfig() {
  const r = await fetch(`${BASE}/config`);
  if (!r.ok) throw new Error(`fetchConfig ${r.status}`);
  return r.json();
}

// ── 聊天记录持久化 ──

export async function fetchChats() {
  const r = await fetch(`${BASE}/chats`);
  if (!r.ok) throw new Error(`fetchChats ${r.status}`);
  return r.json();
}

export async function loadChat(chatId) {
  const r = await fetch(`${BASE}/chats/${encodeURIComponent(chatId)}`);
  if (!r.ok) throw new Error(`loadChat ${r.status}`);
  return r.json();
}

export async function saveChat(chatId, title, messages) {
  const r = await fetch(`${BASE}/chats/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, title, messages }),
  });
  if (!r.ok) throw new Error(`saveChat ${r.status}`);
  return r.json();
}

export async function deleteChat(chatId) {
  const r = await fetch(`${BASE}/chats/${encodeURIComponent(chatId)}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(`deleteChat ${r.status}`);
  return r.json();
}

export async function fetchPapers() {
  const r = await fetch(`${BASE}/papers`);
  if (!r.ok) throw new Error(`fetchPapers ${r.status}`);
  return r.json();
}

export async function uploadPaper(file) {
  const form = new FormData();
  form.append('file', file);
  const r = await fetch(`${BASE}/papers/upload`, { method: 'POST', body: form });
  if (!r.ok) throw new Error(`uploadPaper ${r.status}`);
  return r.json();
}

export async function deletePaper(id) {
  const r = await fetch(`${BASE}/papers/${encodeURIComponent(id)}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(`deletePaper ${r.status}`);
  return r.json();
}

/* SSE 流式对话
   用法：
     await chatStream({question, history, selectedPaperIds}, (evt) => {
       if (evt.type === 'node_start') ...
       if (evt.type === 'node_done')  ...
       if (evt.type === 'answer')     ...
       if (evt.type === 'done')       ...
     });
*/
export async function chatStream({ question, history = [], selectedPaperIds = [], chatId = null }, onEvent) {
  const r = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history, selected_paper_ids: selectedPaperIds, chat_id: chatId }),
  });
  if (!r.ok || !r.body) throw new Error(`chatStream ${r.status}`);

  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE: 事件之间用空行分隔；每行 "data: <json>"
    let idx;
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      const dataLines = chunk
        .split('\n')
        .filter(l => l.startsWith('data:'))
        .map(l => l.slice(5).trim());
      if (!dataLines.length) continue;

      try {
        const evt = JSON.parse(dataLines.join('\n'));
        onEvent(evt);
        if (evt.type === 'done' || evt.type === 'error') return evt;
      } catch (err) {
        console.warn('Bad SSE event:', dataLines, err);
      }
    }
  }
}
