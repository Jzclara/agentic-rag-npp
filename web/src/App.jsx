import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Icon } from './components/Icons.jsx';
import { Sidebar } from './components/Sidebar.jsx';
import { Composer } from './components/Composer.jsx';
import { Message, ThinkingMessage } from './components/Chat.jsx';
import { Inspector } from './components/Inspector.jsx';
import {
  useTweaks, TweaksPanel, TweakSection,
  TweakRadio, TweakToggle, TweakColor,
} from './components/tweaks/TweaksPanel.jsx';
import { PAPERS } from './data.js';

import { fetchPapers, chatStream, fetchChats, loadChat, saveChat, deleteChat } from './api.js';

const TWEAK_DEFAULTS = {
  theme: 'cream',
  accent: 'terracotta',
  showAgentTrace: true,
  citeStyle: 'chip',
  density: 'default',
  inspectorOpen: true,
};

const ACCENTS = {
  terracotta: ['oklch(0.55 0.13 50)',  'oklch(0.92 0.04 50)',  'oklch(0.38 0.10 45)'],
  slate:      ['oklch(0.50 0.09 230)', 'oklch(0.93 0.03 230)', 'oklch(0.35 0.08 230)'],
  ochre:      ['oklch(0.62 0.13 80)',  'oklch(0.94 0.05 80)',  'oklch(0.42 0.10 75)'],
  forest:     ['oklch(0.50 0.10 150)', 'oklch(0.92 0.04 150)', 'oklch(0.35 0.08 150)'],
};

export default function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // theme & accent → CSS vars
  useEffect(() => {
    document.documentElement.dataset.theme = tweaks.theme;
    const [accent, soft, ink] = ACCENTS[tweaks.accent] || ACCENTS.terracotta;
    document.documentElement.style.setProperty('--accent', accent);
    document.documentElement.style.setProperty('--accent-soft', soft);
    document.documentElement.style.setProperty('--accent-ink', ink);
  }, [tweaks.theme, tweaks.accent]);

  const [papers, setPapers] = useState(PAPERS);
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [liveStage, setLiveStage] = useState('');
  const [liveTrace, setLiveTrace] = useState([]);
  const [inspectorTab, setInspectorTab] = useState('trace');

  // ── 多会话管理 ──
  const [chatId, setChatId] = useState(() => 'chat-' + Date.now());
  const [chatList, setChatList] = useState([]);

  // 当前对话的标题：取第一条用户消息
  const chatTitle = useMemo(() => {
    const first = messages.find(m => m.role === 'user');
    return first ? first.text : '';
  }, [messages]);

  // 启动时：从后端加载对话列表，如果有上次的对话则恢复
  useEffect(() => {
    // 从 localStorage 读取上次的 chatId
    const lastId = localStorage.getItem('rag_current_chat_id');

    fetchChats()
      .then(data => {
        setChatList(data.chats || []);
        // 如果有上次打开的对话，自动恢复
        if (lastId && (data.chats || []).some(c => c.id === lastId)) {
          loadChat(lastId).then(chatData => {
            setChatId(lastId);
            setMessages(chatData.messages || []);
          });
        }
      })
      .catch(() => {
        // 后端没启动时，尝试从 localStorage 恢复
        const cached = localStorage.getItem('rag_messages');
        if (cached) {
          try { setMessages(JSON.parse(cached)); } catch {}
        }
      });
  }, []);

  // messages 变化时：写 localStorage + 保存到后端
  const saveTimerRef = useRef(null);
  useEffect(() => {
    // 立即写 localStorage（刷新不丢）
    localStorage.setItem('rag_messages', JSON.stringify(messages));
    localStorage.setItem('rag_current_chat_id', chatId);

    // 防抖保存到后端（避免每条消息都请求）
    if (messages.length > 0) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        saveChat(chatId, chatTitle, messages)
          .then(() => {
            // 保存成功后刷新对话列表
            fetchChats().then(data => setChatList(data.chats || [])).catch(() => {});
          })
          .catch(() => {});
      }, 500);
    }
  }, [messages, chatId]);

  const [focusedMessage, setFocusedMessage] = useState(null);
  const [focusedCite, setFocusedCite] = useState(null);
  const threadRef = useRef(null);

  // 把每条 assistant 消息绑回前一条 user 消息（给 Inspector 的"原始问题"用）
  const messagesWithUser = useMemo(() => {
    let lastUser = '';
    return messages.map(m => {
      if (m.role === 'user') { lastUser = m.text; return m; }
      return { ...m, _userText: lastUser };
    });
  }, [messages]);

  useEffect(() => {
    if (!focusedMessage) {
      const last = [...messagesWithUser].reverse().find(m => m.role === 'assistant');
      if (last) setFocusedMessage(last);
    }
  }, [messagesWithUser]);

  const activePaperCount = papers.filter(p => p.selected).length;

  const handleCiteClick = (n, sources, m) => {
    setInspectorTab('sources');
    setFocusedMessage(m);
    setFocusedCite(n);
  };

  const handleOpenInspector = (m) => {
    setInspectorTab('trace');
    setFocusedMessage(m);
  };

  /* 发送一条问题 —— 调用后端 /api/chat，通过 SSE 实时接收结果。 */
  const sendMessage = async (text) => {
    const userMsg = { id: 'u-' + Date.now(), role: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setBusy(true);
    setLiveTrace([]);

    let answerParts = [];
    let sources = [];
    let traceNodes = [];
    try {
      await chatStream(
        { question: text, history: messages, selectedPaperIds: papers.filter(p => p.selected).map(p => p.id) },
        (evt) => {
          if (evt.type === 'node_start') {
            setLiveStage(evt.name);
            setLiveTrace(prev => [...prev, { name: evt.name, pending: true }]);
          } else if (evt.type === 'node_done') {
            traceNodes.push(evt);
            // 把 liveTrace 里对应的 pending 节点替换为完整的 node_done 数据
            setLiveTrace(prev => {
              const updated = [...prev];
              const idx = updated.findIndex(n => n.name === evt.name && n.pending);
              if (idx >= 0) {
                updated[idx] = evt;
              } else {
                updated.push(evt);
              }
              return updated;
            });
          } else if (evt.type === 'answer') {
            answerParts = evt.parts;
            sources = evt.sources;
          } else if (evt.type === 'done') {
            const assistantMsg = {
              id: 'a-' + Date.now(),
              role: 'assistant',
              standalone: text,
              timing: { totalMs: evt.totalMs, tokens: evt.tokens },
              trace: { status: 'complete', retries: evt.retries, grade: 'relevant', nodes: traceNodes },
              answer: answerParts,
              sources,
            };
            setMessages(prev => [...prev, assistantMsg]);
            setFocusedMessage(assistantMsg);
          }
        }
      );
    } catch (err) {
      console.error('chat failed', err);
    } finally {
      setBusy(false);
      setLiveStage('');
      setLiveTrace([]);
      setTimeout(() => {
        if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight;
      }, 50);
    }
  };

  // 切换到已有对话
  const switchChat = (id) => {
    if (id === chatId) return;
    loadChat(id)
      .then(data => {
        setChatId(id);
        setMessages(data.messages || []);
        setFocusedMessage(null);
      })
      .catch(err => console.error('加载对话失败', err));
  };

  // 新建对话
  const newChat = () => {
    const newId = 'chat-' + Date.now();
    setChatId(newId);
    setMessages([]);
    setFocusedMessage(null);
  };

  // 删除对话
  const handleDeleteChat = (id) => {
    deleteChat(id)
      .then(() => {
        setChatList(prev => prev.filter(c => c.id !== id));
        // 如果删的是当前对话，新建一个
        if (id === chatId) newChat();
      })
      .catch(err => console.error('删除失败', err));
  };

  /* Tweaks 面板：默认隐藏，点击顶栏的设置图标打开 */
  const openTweaks = () => window.postMessage({ type: '__activate_edit_mode' }, '*');

  return (
    <div className={'app density-' + tweaks.density}
         data-inspector={tweaks.inspectorOpen ? 'open' : 'hidden'}
         data-cite-style={tweaks.citeStyle}>
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">α</span>
          <span>论文助读</span>
          <span className="brand-sub">· NPP 文献库</span>
        </div>
        <div className="topbar-right">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)', marginRight: 8 }}>
            <span style={{ color: 'var(--accent)' }}>●</span> hybrid · rerank · parent-child
          </span>
          <button className="icon-btn" title="搜索"><Icon.Search /></button>
          <button className="icon-btn" title="界面设置" onClick={openTweaks}><Icon.Settings /></button>
          <button className="icon-btn"
                  aria-pressed={tweaks.inspectorOpen}
                  onClick={() => setTweak('inspectorOpen', !tweaks.inspectorOpen)}
                  title="切换右侧面板"><Icon.PanelRight /></button>
        </div>
      </header>

      <Sidebar papers={papers} setPapers={setPapers}
               chats={chatList} activeChatId={chatId}
               onNewChat={newChat}
               onSwitchChat={switchChat}
               onDeleteChat={handleDeleteChat} />

      <div className="main">
        <div className="thread-bar">
          <div className="thread-title">
            <h2>用于故障诊断的贝叶斯网络</h2>
            <span className="scope">·  {activePaperCount} 篇在用 · {messagesWithUser.filter(m => m.role === 'user').length} 轮对话</span>
          </div>
          <div className="thread-actions">
            <button className="icon-btn" title="重新运行"><Icon.Refresh /></button>
            <button className="icon-btn" title="复制对话"><Icon.Copy /></button>
          </div>
        </div>
        <div className="thread" ref={threadRef}>
          <div className="thread-inner">
            {messagesWithUser.length === 0 && <EmptyState onPick={sendMessage} papers={papers} />}
            {messagesWithUser.map(m => (
              <Message key={m.id} m={m}
                       onCiteClick={handleCiteClick}
                       onOpenInspector={handleOpenInspector} />
            ))}
            {busy && <ThinkingMessage stage={liveStage} traceLive={liveTrace} />}
          </div>
        </div>
        <Composer scope={activePaperCount} onSend={sendMessage} busy={busy} />
      </div>

      {tweaks.inspectorOpen && (
        <Inspector message={focusedMessage}
                   focusedNum={focusedCite}
                   setFocusedNum={setFocusedCite}
                   activePaperCount={activePaperCount}
                   tab={inspectorTab}
                   setTab={setInspectorTab}
                   busy={busy}
                   liveTrace={liveTrace}
                   liveStage={liveStage} />
      )}

      <TweaksPanel title="Tweaks">
        <TweakSection label="外观">
          <TweakRadio label="主题" value={tweaks.theme}
                      onChange={(v) => setTweak('theme', v)}
                      options={[
                        { value: 'cream', label: '米色' },
                        { value: 'white', label: '白色' },
                        { value: 'dark',  label: '深色' },
                      ]} />
          <TweakColor label="强调色" value={tweaks.accent}
                      onChange={(v) => setTweak('accent', v)}
                      options={[
                        { value: 'terracotta', color: 'oklch(0.55 0.13 50)' },
                        { value: 'slate',      color: 'oklch(0.50 0.09 230)' },
                        { value: 'ochre',      color: 'oklch(0.62 0.13 80)' },
                        { value: 'forest',     color: 'oklch(0.50 0.10 150)' },
                      ]} />
          <TweakRadio label="密度" value={tweaks.density}
                      onChange={(v) => setTweak('density', v)}
                      options={[
                        { value: 'compact', label: '紧凑' },
                        { value: 'default', label: '默认' },
                        { value: 'roomy',   label: '宽松' },
                      ]} />
        </TweakSection>

        <TweakSection label="行为">
          <TweakToggle label="行内显示推理过程"
                       value={tweaks.showAgentTrace}
                       onChange={(v) => setTweak('showAgentTrace', v)} />
          <TweakToggle label="显示右侧面板"
                       value={tweaks.inspectorOpen}
                       onChange={(v) => setTweak('inspectorOpen', v)} />
          <TweakRadio label="引用样式" value={tweaks.citeStyle}
                      onChange={(v) => setTweak('citeStyle', v)}
                      options={[
                        { value: 'chip',     label: '标签' },
                        { value: 'footnote', label: '脚注' },
                      ]} />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

function EmptyState({ onPick, papers }) {
  const examples = [
    { tag: '对比', text: '对比 MFM 与 DBN 在根因分析上的差异。' },
    { tag: '归纳', text: '这几篇论文共同存在哪些局限性？' },
    { tag: '深挖', text: 'LSTM 检测器是如何处理类别不平衡的？' },
    { tag: '综合', text: '数据驱动方法与基于物理的方法在哪些方面达成一致？' },
  ];
  const selectedPapers = papers.filter(p => p.selected);
  return (
    <div className="empty">
      <div className="empty-inner">
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--muted)',
          fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)' }} /> 就绪
        </div>
        <h1>对你的文献库提问。</h1>
        <p className="lede">当前范围内 {selectedPapers.length} 篇文献。助手会改写含糊的追问、在检索效果不佳时自动回退，并为每条结论附上引用。</p>

        {/* 示例问题 */}
        <div className="examples">
          {examples.map((e, i) => (
            <div key={i} className="example-card" onClick={() => onPick(e.text)}>
              <span className="tag">{e.tag}</span>
              {e.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
