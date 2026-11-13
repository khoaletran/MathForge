import React, { useMemo } from 'react';
import katex from 'katex';

interface MathViewProps {
  text: string;
  className?: string;
  displayMode?: boolean;
}

export const MathView: React.FC<MathViewProps> = ({ text, className = '', displayMode = false }) => {
  const renderedContent = useMemo(() => {
    if (!text) return null;

    // Chuẩn hóa Unicode sang chuẩn dựng sẵn (NFC) để tránh lỗi dấu tiếng Việt bị tách rời
    const normalized = text.normalize('NFC');

    // Phân tách chuỗi theo các khối $$...$$ hoặc $...$
    const parts: { isMath: boolean; isDisplay: boolean; content: string }[] = [];
    const regex = /(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(normalized)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          isMath: false,
          isDisplay: false,
          content: normalized.slice(lastIndex, match.index)
        });
      }

      const raw = match[0];
      if (raw.startsWith('$$') && raw.endsWith('$$')) {
        parts.push({
          isMath: true,
          isDisplay: true,
          content: raw.slice(2, -2)
        });
      } else if (raw.startsWith('$') && raw.endsWith('$')) {
        parts.push({
          isMath: true,
          isDisplay: false,
          content: raw.slice(1, -1)
        });
      }

      lastIndex = match.index + raw.length;
    }

    if (lastIndex < normalized.length) {
      parts.push({
        isMath: false,
        isDisplay: false,
        content: normalized.slice(lastIndex)
      });
    }

    return parts.map((part, index) => {
      if (!part.isMath) {
        return (
          <span key={index} className="whitespace-pre-line">
            {part.content}
          </span>
        );
      }

      try {
        const html = katex.renderToString(part.content, {
          displayMode: part.isDisplay || displayMode,
          throwOnError: false,
          trust: true
        });
        return (
          <span
            key={index}
            className={part.isDisplay ? "my-2 block overflow-x-auto text-center" : "inline-block px-0.5 align-middle"}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        );
      } catch (e) {
        return (
          <span key={index} className="text-red-500 font-mono text-xs">
            ${part.content}$
          </span>
        );
      }
    });
  }, [text, displayMode]);

  return <div className={`leading-relaxed ${className}`}>{renderedContent}</div>;
};
