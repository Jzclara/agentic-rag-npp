import React, { useState, useRef } from 'react';
import { Icon } from './Icons.jsx';

/* 左侧栏：文献库 + 最近对话 */
export function Sidebar({ papers, setPapers, chats, activeChatId, onNewChat, onSwitchChat, onDeleteChat }) {
  const allSelected = papers.length > 0 && papers.every(p => p.selected);
  const someSelected = papers.some(p => p.selected) && !allSelected;
  const selectedCount = papers.filter(p => p.selected).length;
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const toggleAll = () => {
    const next = !allSelected;
    setPapers(papers.map(p => ({ ...p, selected: next })));
  };
  const togglePaper = (id) =>
    setPapers(papers.map(p => p.id === id ? { ...p, selected: !p.selected } : p));

  const removePaper = (id, e) => {
    if (e) e.stopPropagation();
    const p = papers.find(x => x.id === id);
    if (!p) return;
    if (!confirm('从文献库中移除「' + p.short + '」？')) return;
    // 接入后端时，这里调用 deletePaper(id) 然后再更新 state
    setPapers(prev => prev.filter(x => x.id !== id));
  };

  /* 把上传的文件转成一个 paper 行。
     这是 UI 占位实现：不解析 PDF，不进向量库。
     接入后端时，把这里换成 uploadPaper(file) 的返回值。 */
  const fileToPaper = (file) => {
    const base = file.name.replace(/\.pdf$/i, '').replace(/[_\-]+/g, ' ').trim();
    const short = base.length > 64 ? base.slice(0, 61) + '…' : base;
    return {
      id: 'u-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6),
      title: base,
      short,
      authors: '已上传',
      venue: '本地 · ' + (file.size > 1024 * 1024
        ? (file.size / 1024 / 1024).toFixed(1) + ' MB'
        : Math.round(file.size / 1024) + ' KB'),
      year: new Date().getFullYear(),
      pages: null,
      tag: '新增',
      selected: true,
    };
  };

  const addFiles = (fileList) => {
    const pdfs = Array.from(fileList || []).filter(f =>
      /\.pdf$/i.test(f.name) || f.type === 'application/pdf'
    );
    if (!pdfs.length) return;
    const next = pdfs.map(fileToPaper);
    setPapers(prev => [...prev, ...next]);
  };

  const openPicker = () => fileInputRef.current && fileInputRef.current.click();
  const onPicked = (e) => {
    addFiles(e.target.files);
    e.target.value = '';
  };
  const onDragOver = (e) => { e.preventDefault(); e.stopPropagation(); setDragOver(true); };
  const onDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); setDragOver(false); };
  const onDrop = (e) => {
    e.preventDefault(); e.stopPropagation(); setDragOver(false);
    addFiles(e.dataTransfer && e.dataTransfer.files);
  };

  return (
    <aside className="sidebar">
      <button className="new-chat" onClick={onNewChat}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Icon.Plus /> 新建对话</span>
        <span className="kbd">⌘N</span>
      </button>

      <div className="sidebar-scroll">
        <section className="side-section">
          <div className="side-label">
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }} onClick={toggleAll}>
              <span className={'checkbox ' + (allSelected ? 'checked' : '')}
                    style={someSelected ? { background: 'var(--muted-2)', borderColor: 'var(--muted-2)' } : null}>
                <Icon.Check />
              </span>
              文献库
            </span>
            <span className="count">{selectedCount}/{papers.length}</span>
          </div>
          <div className="papers">
            {papers.map(p => (
              <div key={p.id}
                   className={'paper-row ' + (p.selected ? 'selected' : '')}
                   onClick={() => togglePaper(p.id)}>
                <span className={'checkbox ' + (p.selected ? 'checked' : '')}><Icon.Check /></span>
                <div style={{ minWidth: 0 }}>
                  <div className="paper-title">{p.short}</div>
                  <div className="paper-meta">{p.authors} · {p.year}</div>
                </div>
                <span className="paper-badge">{p.tag}</span>
                <button className="paper-remove"
                        title="从文献库中移除"
                        onClick={(e) => removePaper(p.id, e)}>
                  <Icon.X />
                </button>
              </div>
            ))}
          </div>
          <div className={'upload-zone' + (dragOver ? ' is-drag' : '')}
               onClick={openPicker}
               onDragOver={onDragOver}
               onDragEnter={onDragOver}
               onDragLeave={onDragLeave}
               onDrop={onDrop}>
            <div className="plus">＋</div>
            <div>{dragOver ? '松开以添加 PDF' : '拖入 PDF 加入文献库'}</div>
            <input ref={fileInputRef}
                   type="file"
                   accept="application/pdf,.pdf"
                   multiple
                   onChange={onPicked}
                   style={{ display: 'none' }} />
          </div>
        </section>

        <section className="side-section">
          <div className="side-label">
            <span>最近对话</span>
            <span className="count">{chats.length}</span>
          </div>
          <div className="chats">
            {chats.map(c => (
              <div key={c.id}
                   className={'chat-row ' + (c.id === activeChatId ? 'active' : '')}
                   onClick={() => onSwitchChat && onSwitchChat(c.id)}>
                <span className="dot" />
                <span className="title">{c.title}</span>
                <button className="paper-remove"
                        title="删除对话"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm('删除这个对话？')) onDeleteChat && onDeleteChat(c.id);
                        }}>
                  <Icon.X />
                </button>
              </div>
            ))}
            {chats.length === 0 && (
              <div style={{ color: 'var(--muted)', fontSize: 12, padding: '8px 12px' }}>
                暂无对话记录
              </div>
            )}
          </div>
        </section>
      </div>
    </aside>
  );
}
