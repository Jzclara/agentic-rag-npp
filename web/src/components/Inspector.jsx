import React, { useState, useEffect } from 'react';
import { PAPERS, SOURCES_BY_KEY } from '../data.js';
import { fetchEvals, fetchConfig } from '../api.js';
import { PdfViewer } from './PdfViewer.jsx';

function AgentTraceView({ message }) {
  const t = message.trace;
  const totalMs = t.nodes.reduce((a, b) => a + (b.ms || 0), 0);
  const statusLabel = t.retries > 0 ? `1 次重试 · ${t.grade}` : `${t.grade}`;
  const statusCls = t.retries > 0 ? 'retry' : '';

  return (
    <div className="trace-graph">
      <div className="trace-graph-head">
        <h3>本次推理</h3>
        <span className={'run-status ' + statusCls}><span className="led" />{statusLabel}</span>
      </div>

      <div style={{ marginBottom: 14 }}>
        <div style={{
          fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--muted)',
          textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4,
        }}>原始问题</div>
        <div style={{
          fontSize: 13, color: 'var(--ink)', fontFamily: 'var(--font-serif)', lineHeight: 1.55,
        }}>“{message._userText}”</div>
        {message.standalone && message.standalone !== message._userText && (
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px dashed var(--border)' }}>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--muted)',
              textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4,
            }}>改写后</div>
            <div style={{ fontSize: 12.5, color: 'var(--ink-soft)', lineHeight: 1.5 }}>{message.standalone}</div>
          </div>
        )}
      </div>

      <div className="nodes">
        {t.nodes.map((n, i) => {
          const cls = n.retry ? 'retry' : 'done';
          return (
            <div key={n.id} className={'node ' + cls}>
              <div className="node-dot">{n.retry ? '↻' : (i + 1)}</div>
              <div className="node-body">
                <div className="node-name">
                  <span>{n.name}</span>
                  <span className="tag">{n.tag}</span>
                  {n.verdict === 'insufficient' && <span className="tag" style={{ background: 'var(--warn-soft)', color: 'var(--warn)' }}>不足</span>}
                  {n.verdict === 'relevant' && <span className="tag" style={{ background: 'var(--success-soft)', color: 'var(--success)' }}>相关</span>}
                </div>
                <div className="node-detail">
                  {n.detail}
                  {n.quote && <div className="quote" style={{ marginTop: 4 }}>“{n.quote}”</div>}
                  {n.subnodes && (
                    <div className="subnodes">
                      {n.subnodes.map((s, k) => (
                        <div key={k} className="subnode">
                          <span className="check">✓</span>
                          <span>{s}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="node-ms">{n.ms}ms</div>
            </div>
          );
        })}
      </div>

      {message.eval && (
        <div style={{
          marginTop: 14, paddingTop: 12, borderTop: '1px dashed var(--border)',
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--muted)',
            textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8,
          }}>本次评估 (Ragas)</div>
          <div style={{ display: 'flex', gap: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 2 }}>忠实度</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: message.eval.faithfulness >= 0.7 ? 'var(--success)' : 'var(--warn)' }}>
                {message.eval.faithfulness.toFixed(2)}
              </div>
              <div className="bar" style={{ marginTop: 4 }}><div style={{ width: (message.eval.faithfulness * 100) + '%' }} /></div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 2 }}>相关性</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: message.eval.answer_relevancy >= 0.7 ? 'var(--success)' : 'var(--warn)' }}>
                {message.eval.answer_relevancy.toFixed(2)}
              </div>
              <div className="bar" style={{ marginTop: 4 }}><div style={{ width: (message.eval.answer_relevancy * 100) + '%' }} /></div>
            </div>
          </div>
        </div>
      )}

      <div style={{
        marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)',
      }}>
        <span>总计 · {(totalMs / 1000).toFixed(2)}s</span>
        <span>{message.timing.tokens} tokens · {t.nodes.length} 步</span>
      </div>
    </div>
  );
}

/* 来源弹窗：直接显示 PDF 原文并高亮匹配文本 */
function SourceModal({ source, onClose }) {
  return (
    <PdfViewer
      fileName={source.fileName}
      page={source.page}
      onClose={onClose}
      highlightText={source.full_text || source.quote}
      sourceInfo={source}
    />
  );
}

function SourcesView({ message, focusedNum, setFocusedNum }) {
  const sources = (message && (SOURCES_BY_KEY[message.sourcesKey] || message.sources)) || [];
  const [selectedSource, setSelectedSource] = useState(null);

  if (!sources.length) return <div style={{ color: 'var(--muted)', textAlign: 'center', padding: 32 }}>暂无引用来源。</div>;

  return (
    <div className="inspector-section">
      <h3>检索到的上下文 · {sources.length} 段</h3>
      {sources.map(s => {
        const paper = PAPERS.find(p => p.id === s.paperId);
        const focused = focusedNum === s.n;
        return (
          <div key={s.n}
               className="src-item"
               id={'src-' + s.n}
               style={{
                 cursor: 'pointer',
                 ...(focused ? { background: 'var(--accent-soft)', borderRadius: 8, padding: 10, margin: '0 -10px' } : {}),
               }}
               onClick={() => setSelectedSource(s)}
               onMouseEnter={() => setFocusedNum && setFocusedNum(s.n)}>
            <div className="head">
              <span className="num">{s.n}</span>
              <div className="meta">
                <span className="file">{paper ? paper.short : s.fileName}</span>
                <span className="page">p.{s.page}</span>
              </div>
              <span className="score">{s.score.toFixed(3)}</span>
            </div>
            <div className="quote">{s.quote}</div>
          </div>
        );
      })}

      {selectedSource && (
        <SourceModal source={selectedSource} onClose={() => setSelectedSource(null)} />
      )}
    </div>
  );
}

function EvalView({ activePaperCount }) {
  const [evals, setEvals] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadEvals = () => {
    setLoading(true);
    fetchEvals()
      .then(data => setEvals(data.evals || []))
      .catch(() => setEvals([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadEvals();
    fetchConfig().then(setConfig).catch(() => setConfig(null));
    const timer = setInterval(loadEvals, 15000);
    return () => clearInterval(timer);
  }, []);

  // 找最新的 agentic 和 baseline 评估结果
  const latest = evals[0];
  const baseline = evals.find(e => e.run_name && e.run_name.includes('baseline'));

  return (
    <>
      <div className="inspector-section">
        <h3 style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          Ragas 评估
          <button onClick={loadEvals} disabled={loading}
            style={{
              background: 'none', border: '1px solid var(--border)', borderRadius: 6,
              padding: '2px 8px', fontSize: 11, color: 'var(--muted)', cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
            }}>
            {loading ? '...' : '刷新'}
          </button>
        </h3>
        {loading ? (
          <div style={{ color: 'var(--muted)', fontSize: 13, padding: 16 }}>加载中...</div>
        ) : !latest ? (
          <div style={{ color: 'var(--muted)', fontSize: 13, padding: 16, lineHeight: 1.6 }}>
            尚未运行评估。<br />
            <span style={{ fontSize: 11.5, fontFamily: 'var(--font-mono)' }}>
              运行方式：python -m src.evals.run_ragas
            </span>
          </div>
        ) : (
          <>
            <div className="metric-row">
              <span className="label">忠实度 faithfulness</span>
              <span>
                <span className="val">{latest.scores.faithfulness.toFixed(2)}</span>
                {baseline && (
                  <span className="diff">
                    {(latest.scores.faithfulness - baseline.scores.faithfulness) >= 0 ? '+' : ''}
                    {(latest.scores.faithfulness - baseline.scores.faithfulness).toFixed(2)}
                  </span>
                )}
              </span>
            </div>
            <div className="bar"><div style={{ width: (latest.scores.faithfulness * 100) + '%' }} /></div>
            <div className="metric-row" style={{ marginTop: 10 }}>
              <span className="label">回答相关性 relevancy</span>
              <span>
                <span className="val">{latest.scores.answer_relevancy.toFixed(2)}</span>
                {baseline && (
                  <span className="diff">
                    {(latest.scores.answer_relevancy - baseline.scores.answer_relevancy) >= 0 ? '+' : ''}
                    {(latest.scores.answer_relevancy - baseline.scores.answer_relevancy).toFixed(2)}
                  </span>
                )}
              </span>
            </div>
            <div className="bar"><div style={{ width: (latest.scores.answer_relevancy * 100) + '%' }} /></div>
            <div style={{ marginTop: 12, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)' }}>
              {latest.run_name} · {latest.model} · {latest.num_samples} 条样本
              {baseline && (<><br />基线 · {baseline.scores.faithfulness.toFixed(2)} / {baseline.scores.answer_relevancy.toFixed(2)}</>)}
            </div>
          </>
        )}
      </div>

      <div className="inspector-section">
        <h3>当前范围</h3>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--ink-soft)', lineHeight: 1.7 }}>
          {config ? (
            <>
              已选 {config.paper_count} / {config.paper_count} 篇<br />
              检索器 · <span style={{ color: 'var(--accent)' }}>{config.retriever}</span> ({config.retriever_detail})<br />
              切块 · {config.chunk_strategy} · {config.child_chunk_size}/{config.parent_chunk_size}<br />
              重排 · {config.reranker_model} · top-{config.reranker_top_n}<br />
              最大重试 · {config.max_retries}<br />
              模型 · {config.llm_model}
            </>
          ) : (
            <>
              已选 {activePaperCount} / {PAPERS.length} 篇<br />
              后端未连接，显示默认值
            </>
          )}
        </div>
      </div>

      {evals.length > 0 && (
        <div className="inspector-section">
          <h3>评估记录 · {evals.length} 次</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {evals.slice(0, 8).map((e, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 0', borderTop: '1px dashed var(--border)',
                fontSize: 12.5, color: 'var(--ink-soft)',
              }}>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.run_name}
                </span>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--muted)',
                  flexShrink: 0, marginLeft: 8,
                }}>
                  {e.scores.faithfulness.toFixed(2)} / {e.scores.answer_relevancy.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

/* 推理进行中的实时 trace 视图 */
function LiveTraceView({ liveTrace, liveStage }) {
  return (
    <div className="trace-graph">
      <div className="trace-graph-head">
        <h3>推理中…</h3>
        <span className="run-status"><span className="led blink" />{liveStage || '准备中'}</span>
      </div>
      <div className="nodes">
        {liveTrace.map((n, i) => {
          const isPending = n.pending;
          const cls = n.retry ? 'retry' : isPending ? 'pending' : 'done';
          return (
            <div key={i} className={'node ' + cls}>
              <div className="node-dot">{isPending ? '…' : (n.retry ? '↻' : (i + 1))}</div>
              <div className="node-body">
                <div className="node-name">
                  <span>{n.name}</span>
                  {n.tag && <span className="tag">{n.tag}</span>}
                  {n.verdict === 'insufficient' && <span className="tag" style={{ background: 'var(--warn-soft)', color: 'var(--warn)' }}>不足</span>}
                  {n.verdict === 'relevant' && <span className="tag" style={{ background: 'var(--success-soft)', color: 'var(--success)' }}>相关</span>}
                </div>
                <div className="node-detail">
                  {isPending
                    ? <span style={{ color: 'var(--muted)' }}>执行中…</span>
                    : n.detail}
                  {n.quote && <div className="quote" style={{ marginTop: 4 }}>"{n.quote}"</div>}
                  {n.subnodes && (
                    <div className="subnodes">
                      {n.subnodes.map((s, k) => (
                        <div key={k} className="subnode">
                          <span className="check">✓</span>
                          <span>{s}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              {!isPending && n.ms != null && <div className="node-ms">{n.ms}ms</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function Inspector({ message, focusedNum, setFocusedNum, activePaperCount, tab, setTab, busy, liveTrace, liveStage }) {
  return (
    <aside className="inspector">
      <div className="inspector-tabs">
        <button className={'inspector-tab ' + (tab === 'trace' ? 'active' : '')}
                onClick={() => setTab('trace')}>推理过程</button>
        <button className={'inspector-tab ' + (tab === 'sources' ? 'active' : '')}
                onClick={() => setTab('sources')}>
          引用来源 <span className="num">{message ? ((SOURCES_BY_KEY[message.sourcesKey] || message.sources || []).length) : 0}</span>
        </button>
      </div>
      <div className="inspector-body">
        {tab === 'trace' && busy && liveTrace && liveTrace.length > 0 && (
          <LiveTraceView liveTrace={liveTrace} liveStage={liveStage} />
        )}
        {tab === 'trace' && !busy && message && <AgentTraceView message={message} />}
        {tab === 'sources' && <SourcesView message={message} focusedNum={focusedNum} setFocusedNum={setFocusedNum} />}
      </div>
    </aside>
  );
}
