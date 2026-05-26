import React, { useState, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

function norm(text) {
  return text.replace(/\s+/g, ' ').trim().toLowerCase();
}

export function PdfViewer({ fileName, page, onClose, highlightText, sourceInfo }) {
  const [numPages, setNumPages] = useState(null);
  const [currentPage, setCurrentPage] = useState(page || 1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pageRef = useRef(null);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    if (page > numPages) setCurrentPage(numPages);
  };

  const onDocumentLoadError = (err) => {
    setError('PDF 加载失败：' + err.message);
    setLoading(false);
  };

  const goPage = (n) => {
    if (n >= 1 && n <= numPages) setCurrentPage(n);
  };

  const highlightMatches = useCallback(() => {
    if (!highlightText || !pageRef.current) return;

    const textLayer = pageRef.current.querySelector('.react-pdf__Page__textContent');
    if (!textLayer) return;

    const spans = Array.from(textLayer.querySelectorAll('span'));
    if (!spans.length) return;

    spans.forEach(s => s.classList.remove('pdf-highlight'));

    // Build full text with position tracking
    let fullText = '';
    const ranges = [];
    spans.forEach(span => {
      const start = fullText.length;
      fullText += span.textContent;
      ranges.push({ span, start, end: fullText.length });
    });

    const fullNorm = norm(fullText);
    const chunkNorm = norm(highlightText);
    if (!chunkNorm) return;

    // Try progressively shorter prefixes to find a match
    let bestPos = -1;
    const tryLengths = [200, 100, 60, 35];
    for (const len of tryLengths) {
      if (chunkNorm.length < len) continue;
      const fragment = chunkNorm.substring(0, len);
      bestPos = fullNorm.indexOf(fragment);
      if (bestPos !== -1) break;
    }

    // Fallback: try to find any 25-char window from the chunk
    if (bestPos === -1) {
      for (let i = 0; i < chunkNorm.length - 25; i += 20) {
        const fragment = chunkNorm.substring(i, i + 25);
        bestPos = fullNorm.indexOf(fragment);
        if (bestPos !== -1) break;
      }
    }

    if (bestPos === -1) return;

    const matchEnd = Math.min(bestPos + chunkNorm.length + 50, fullText.length);
    let firstHighlight = null;

    ranges.forEach(({ span, start, end }) => {
      if (start < matchEnd && end > bestPos && span.textContent.trim()) {
        span.classList.add('pdf-highlight');
        if (!firstHighlight) firstHighlight = span;
      }
    });

    if (firstHighlight) {
      setTimeout(() => {
        firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 150);
    }
  }, [highlightText]);

  const onPageRenderSuccess = useCallback(() => {
    setTimeout(highlightMatches, 250);
  }, [highlightMatches]);

  return (
    <div className="pdf-overlay" onClick={onClose}>
      <div className="pdf-container" onClick={(e) => e.stopPropagation()}>
        {/* 顶部工具栏 */}
        <div className="pdf-toolbar">
          <div className="pdf-title">
            <span style={{ fontWeight: 600 }}>{fileName}</span>
            {sourceInfo && (
              <span style={{
                marginLeft: 10, fontSize: 11, color: 'var(--muted)',
                fontFamily: 'var(--font-mono)',
              }}>
                来源 [{sourceInfo.n}] · 相关度 {sourceInfo.score.toFixed(3)}
              </span>
            )}
          </div>
          <div className="pdf-nav">
            <button disabled={currentPage <= 1} onClick={() => goPage(currentPage - 1)}>←</button>
            <span>
              第 <input
                type="number"
                value={currentPage}
                min={1}
                max={numPages || 1}
                onChange={(e) => goPage(parseInt(e.target.value) || 1)}
                style={{ width: 40, textAlign: 'center' }}
              /> / {numPages || '?'} 页
            </span>
            <button disabled={currentPage >= numPages} onClick={() => goPage(currentPage + 1)}>→</button>
          </div>
          <button className="pdf-close" onClick={onClose}>✕</button>
        </div>

        {/* PDF 渲染区 */}
        <div className="pdf-body">
          {error && <div className="pdf-error">{error}</div>}
          {loading && !error && <div className="pdf-loading">加载 PDF 中...</div>}
          <div ref={pageRef}>
            <Document
              file={`/api/pdf/${encodeURIComponent(fileName)}`}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading=""
            >
              <Page
                pageNumber={currentPage}
                width={Math.min(window.innerWidth * 0.7, 900)}
                renderTextLayer={true}
                renderAnnotationLayer={false}
                onRenderSuccess={onPageRenderSuccess}
              />
            </Document>
          </div>
        </div>
      </div>
    </div>
  );
}
