import React, { useState, useEffect, useRef } from 'react';
import { Icon } from './Icons.jsx';
import { SUGGESTIONS } from '../data.js';

/* 底部输入框 + 候选建议 */
export function Composer({ scope, onSend, onStop, busy }) {
  const [val, setVal] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto';
      ref.current.style.height = Math.min(ref.current.scrollHeight, 200) + 'px';
    }
  }, [val]);

  const submit = () => {
    if (!val.trim() || busy) return;
    onSend(val.trim());
    setVal('');
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          ref={ref}
          rows={1}
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={onKey}
          placeholder="就这些文献继续提问……"
          disabled={busy}
        />
        <div className="composer-actions">
          <div className="left">
            <span className="scope-chip"><span className="num">{scope}</span> 篇在用</span>
          </div>
          {busy ? (
            // 生成中：发送按钮变成「停止」按钮，点击中断本次请求
            <button className="send-btn stop-btn" onClick={onStop} title="停止生成">
              <Icon.Stop />
            </button>
          ) : (
            <button className="send-btn" onClick={submit} disabled={!val.trim()}>
              <Icon.Send />
            </button>
          )}
        </div>
      </div>
      <div className="suggestions">
        {SUGGESTIONS.map((s, i) => (
          <button key={i} className="suggestion"
                  onClick={() => { setVal(s); ref.current && ref.current.focus(); }}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
