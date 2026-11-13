import React, { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface MathViewProps {
  text: string;
  className?: string;
  displayMode?: boolean;
  onNumberEdit?: (start: number, end: number, value: string, target: HTMLElement) => void;
}

const legacyFormula = /\\(?:frac\{[^{}]+\}\{[^{}]+\}|sqrt(?:\[[^\]]+\])?\{[^{}]+\}|infty\b)/g;

function formatExistingMath(text: string): string {
  return text.split(/(\$\$[\s\S]*?\$\$|\$[^$]+\$)/g).map(part => {
    if (part.startsWith('$')) return part;
    return part
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(legacyFormula, formula => `$${formula}$`);
  }).join('');
}

export const MathView: React.FC<MathViewProps> = ({ text, className = '', displayMode = false, onNumberEdit }) => {
  const renderedContent = useMemo(() => {
    if (!text) return null;

    // Chuẩn hóa Unicode sang chuẩn dựng sẵn (NFC) để tránh lỗi dấu tiếng Việt bị tách rời
    const normalized = onNumberEdit ? text.normalize('NFC') : formatExistingMath(text.normalize('NFC'));

    // Phân tách chuỗi theo các khối $$...$$ hoặc $...$
    const parts: { isMath: boolean; isDisplay: boolean; content: string; start: number }[] = [];
    const regex = /(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(normalized)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          isMath: false,
          isDisplay: false,
          content: normalized.slice(lastIndex, match.index), start: lastIndex
        });
      }

      const raw = match[0];
      if (raw.startsWith('$$') && raw.endsWith('$$')) {
        parts.push({
          isMath: true,
          isDisplay: true,
          content: raw.slice(2, -2), start: match.index + 2
        });
      } else if (raw.startsWith('$') && raw.endsWith('$')) {
        parts.push({
          isMath: true,
          isDisplay: false,
          content: raw.slice(1, -1), start: match.index + 1
        });
      }

      lastIndex = match.index + raw.length;
    }

    if (lastIndex < normalized.length) {
      parts.push({
        isMath: false,
        isDisplay: false,
        content: normalized.slice(lastIndex), start: lastIndex
      });
    }

    return parts.map((part, index) => {
      if (!part.isMath) {
        return (
          <span key={index} className="whitespace-pre-line">
            {onNumberEdit ? part.content.split(/(\\+infty(?![a-zA-Z])|\d+(?:[.,]\d+)*|[\p{L}\p{M}]+|[^\s\p{L}\p{M}\d])/u).map((piece, i, pieces) => {
              if (i % 2 === 0) return piece;
              const start = part.start + pieces.slice(0, i).join('').length;
              return <button key={i} type="button" className="editable-math-number"
                aria-label={`Sửa ${piece}`}
                onClick={event => onNumberEdit(start, start + piece.length, piece, event.currentTarget)}
                onKeyDown={event => {
                  if (event.key === "Enter") onNumberEdit(start, start + piece.length, piece, event.currentTarget);
                }}>{piece.replace(/^\\+infty$/, '∞')}</button>;
            }) : part.content.replace(/\\+infty(?![a-zA-Z])/g, '∞')}
          </span>
        );
      }

      try {
        const numbers = new Map<string, { start: number; value: string }>();
        const formula = onNumberEdit ? part.content.replace(
          /\\(?:begin|end|operatorname|text|mathrm|mathbb)\{[^{}]*\}|\\[a-zA-Z]+|\\[^a-zA-Z]|\d+(?:(?:[.,]|\{,\})\d+)*|[a-zA-Z=+*-]/g,
          (token, offset: number) => {
            if (token.startsWith('\\') && !/^\\(?:alpha|beta|gamma|delta|theta|lambda|mu|pi|sigma|omega|infty|times|cdot|div|pm|leq?|geq?|neq|approx|in|notin)$/.test(token)) return token;
            const key = `editable-number-${part.start + offset}`;
            numbers.set(key, { start: part.start + offset, value: token });
            return `{\\htmlClass{editable-math-number ${key}}{${token}}}`;
          },
        ) : part.content;
        const html = katex.renderToString(formula.replace(/\\{2,}infty(?![a-zA-Z])/g, () => '\\infty'), {
          displayMode: part.isDisplay || displayMode,
          throwOnError: false,
          strict: code => code === "htmlExtension" && onNumberEdit ? "ignore" : "warn",
          trust: context => context.command === '\\htmlClass' &&
            'class' in context && /^editable-math-number editable-number-\d+$/.test(context.class) &&
            numbers.has(context.class.split(' ')[1])
        });
        return (
          <span
            key={index}
            className={part.isDisplay || displayMode ? "my-2 block overflow-x-auto py-1 text-center" : "inline-block px-0.5 py-0.5 align-middle overflow-visible"}
            onClick={onNumberEdit ? event => {
              const direct = (event.target as Element).closest<HTMLElement>('.editable-math-number');
              // KaTeX can place matrix spacing or a strut above the visible digit.
              const target = direct ?? Array.from(event.currentTarget.querySelectorAll<HTMLElement>('.editable-math-number'))
                .find(element => {
                  const rect = element.getBoundingClientRect();
                  return event.clientX >= rect.left && event.clientX <= rect.right &&
                    event.clientY >= rect.top && event.clientY <= rect.bottom;
                });
              const key = Array.from(target?.classList ?? []).find(name => numbers.has(name));
              const number = key ? numbers.get(key) : undefined;
              if (target && number) {
                event.stopPropagation();
                onNumberEdit(number.start, number.start + number.value.length, number.value, target);
              }
            } : undefined}
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
  }, [text, displayMode, onNumberEdit]);

  return <div className={`leading-relaxed ${className}`}>{renderedContent}</div>;
};
