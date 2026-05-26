import React, { useState } from 'react';
import { Icon } from './Icons.jsx';
import { PAPERS, SOURCES_BY_KEY } from '../data.js';

/* 把答案的 {p, b, cite, br} 段拼成 DOM */
function AnswerBody({ parts, activeCite, setActiveCite, onCiteClick }) {
  const out = [];
  parts.forEach((seg, i) => {
    if (seg.br) { out.push(<br key={'br' + i} />); return; }
    let node = seg.p;
    if (seg.b) node = <strong key={'b' + i}>{node}</strong>;
    out.push(<span key={'s' + i}>{node}</span>);
    if (seg.cite != null) {
      const n = seg.cite;
      out.push(
        <sup key={'c' + i}
             className={'cite ' + (activeCite === n ? 'active' : '')}
             onMouseEnter={() => setActiveCite(n)}
             onMouseLeave={() => setActiveCite(null)}
             onClick={() => onCiteClick(n)}>
          {n}
        </sup>
      );
    }
  });
  return <div className="answer">{out}</div>;
}

/* trace 摘要行（一行式，点开打开 Inspector） */
function TraceSummary({ trace, onOpenInspector }) {
  const totalMs = trace.nodes.reduce((a, b) => a + (b.ms || 0), 0);
  const seen = {};
  trace.nodes.forEach(n => { seen[n.name] = (seen[n.name] || 0) + 1; });
  const steps = [];
  ['rewrite', 'retrieve', 'grade', 'generate', 'fallback'].forEach(name => {
    if (seen[name]) steps.push(seen[name] > 1 ? `${name} ×${seen[name]}` : name);
  });
  const cls = trace.retries > 0 ? 'retried' : '';
  return (
    <button className={'trace-line ' + cls} onClick={onOpenInspector}>
      <span className="pulse" />
      <span className="steps">
        {steps.map((s, i) => (
          <span key={s} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <span className="step">{s}</span>
            {i < steps.length - 1 && <span className="sep">→</span>}
          </span>
        ))}
      </span>
      <span className="ms">
        {trace.retries > 0 && <span style={{ color: 'var(--warn)', marginRight: 8 }}>1 次重试</span>}
        {(totalMs / 1000).toFixed(2)}s
      </span>
      <span className="chev"><Icon.Chevron /></span>
    </button>
  );
}

/* 答案下方的引用卡片列表 */
function SourcesStrip({ sources, onCiteClick }) {
  const top = sources.slice(0, 4);
  return (
    <div className="sources-strip">
      {top.map(s => (
        <div key={s.n}
             className="source-card"
             onMouseEnter={() => onCiteClick(s.n, false)}
             onClick={() => onCiteClick(s.n, true)}>
          <div className="src-head">
            <span className="src-num">{s.n}</span>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {s.fileName}
            </span>
            <span>p.{s.page}</span>
          </div>
          <div className="src-title">{PAPERS.find(p => p.id === s.paperId)?.short || s.fileName}</div>
          <div className="src-snippet">{s.quote}</div>
        </div>
      ))}
    </div>
  );
}

/* 单条消息：用户 or 助手 */
export function Message({ m, onCiteClick, onOpenInspector }) {
  const [activeCite, setActiveCite] = useState(null);

  if (m.role === 'user') {
    return (
      <div className="turn-user">
        <div className="bubble">{m.text}</div>
      </div>
    );
  }
  const sources = SOURCES_BY_KEY[m.sourcesKey] || m.sources || [];
  return (
    <div className="turn-assistant">
      <div className="assistant-head">
        <span className="avatar">α</span>
        <span className="name">论文助读</span>
        <span className="timing">
          {(m.timing.totalMs / 1000).toFixed(2)}s · {m.timing.tokens} tokens · {m.trace.nodes.length} 步
        </span>
      </div>

      <TraceSummary trace={m.trace} onOpenInspector={() => onOpenInspector(m)} />

      <AnswerBody
        parts={m.answer}
        activeCite={activeCite}
        setActiveCite={setActiveCite}
        onCiteClick={(n) => onCiteClick(n, sources, m)}
      />

      {/* 引用来源已在右侧 Inspector 面板展示，聊天框内不再重复 */}
    </div>
  );
}

/* 思考中（busy 时显示） */
export function ThinkingMessage({ stage, traceLive }) {
  return (
    <div className="turn-assistant">
      <div className="assistant-head">
        <span className="avatar">α</span>
        <span className="name">论文助读</span>
        <span className="timing">
          <span className="thinking-dots"><span /><span /><span /></span>
        </span>
      </div>
      <div className="trace-line">
        <span className="pulse" style={{ background: 'var(--info)', animation: 'pulse 1.2s infinite' }} />
        <span className="steps">
          {traceLive.map((n, i) => (
            <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className="step"
                    style={i === traceLive.length - 1 ? { color: 'var(--accent)', fontWeight: 600 } : null}>
                {n.name}
              </span>
              {i < traceLive.length - 1 && <span className="sep">→</span>}
            </span>
          ))}
        </span>
        <span className="ms" style={{ color: 'var(--info)' }}>
          {stage}
          <span className="thinking-dots" style={{ marginLeft: 6 }}><span /><span /><span /></span>
        </span>
      </div>
    </div>
  );
}
