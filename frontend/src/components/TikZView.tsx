import React, { useState, useMemo } from 'react';
import { MathView } from './MathView';
import { Code, Eye, Copy, Check } from 'lucide-react';

interface TikZViewProps {
  tikzCode: string;
  className?: string;
  printMode?: boolean; // Khi in A4: gọn gàng, nền trắng, không nút bấm
}

export const TikZView: React.FC<TikZViewProps> = ({
  tikzCode,
  className = '',
  printMode = false,
}) => {
  const [showRaw, setShowRaw] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(tikzCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Phân tích mã TikZ để nhận diện loại hình: Bảng biến thiên hay Hình học không gian
  const parsedData = useMemo(() => {
    if (!tikzCode) return null;
    const code = tikzCode.trim();

    // 1. Nhận diện Bảng biến thiên tkz-tab
    if (code.includes('\\tkzTabInit') || code.includes('tkzTab')) {
      try {
        // Trích xuất dòng giá trị x
        // Cú pháp: { $-\infty$, ${x1}$, ${x2}$, $+\infty$ }
        const xMatch = code.match(/\{(\s*-\s*\\infty[\s\S]*?\+\s*\\infty\s*)\}/);
        let xItems: string[] = [];
        if (xMatch) {
          xItems = xMatch[1].split(',').map(s => s.trim().replace(/^\$|\$$/g, ''));
        }

        // Trích xuất dấu y' (\tkzTabLine{...})
        const lineMatch = code.match(/\\tkzTabLine\{([^}]+)\}/);
        let signs: string[] = [];
        if (lineMatch) {
          // Bỏ dấu phẩy ở đầu và cuối nếu có
          signs = lineMatch[1].split(',').filter(s => s.trim().length > 0);
        }

        // Trích xuất biến thiên y (\tkzTabVar{...})
        const varMatch = code.match(/\\tkzTabVar\{([^}]+)\}/);
        let varNodes: { type: string; val: string; val2?: string }[] = [];
        if (varMatch) {
          // Tách các cụm dạng: +/ $+\infty$, -/ ${y1}, -D+/ $-\infty$ / $+\infty$
          const parts = varMatch[1].split(',').map(p => p.trim()).filter(Boolean);
          for (const p of parts) {
            if (p.includes('-D+') || p.includes('+D-')) {
              // Tiệm cận đứng 2 gạch
              const slashParts = p.split('/').map(s => s.trim().replace(/^\$|\$$/g, ''));
              varNodes.push({
                type: 'double_bar',
                val: slashParts[1] || '',
                val2: slashParts[2] || '',
              });
            } else if (p.startsWith('+/')) {
              const val = p.substring(2).trim().replace(/^\$|\$$/g, '');
              varNodes.push({ type: 'up', val });
            } else if (p.startsWith('-/')) {
              const val = p.substring(2).trim().replace(/^\$|\$$/g, '');
              varNodes.push({ type: 'down', val });
            }
          }
        }

        return {
          category: 'table',
          xItems,
          signs,
          varNodes,
        };
      } catch (e) {
        console.warn('Không thể bóc tách tkz-tab:', e);
      }
    }

    // 2. Nhận diện Hình chóp tam giác S.ABC
    if (code.includes('chop_tam_giac') || (code.includes('(A)') && code.includes('(B)') && code.includes('(C)') && code.includes('(S)') && !code.includes('(D)'))) {
      return { category: 'chop_tam_giac' };
    }

    // 3. Nhận diện Hình chóp tứ giác S.ABCD
    if (code.includes('chop_tu_giac') || (code.includes('(A)') && code.includes('(B)') && code.includes('(C)') && code.includes('(D)') && code.includes('(S)'))) {
      return { category: 'chop_tu_giac' };
    }

    // 4. Nhận diện Hình lăng trụ tam giác ABC.A'B'C'
    if (code.includes('lang_tru') || (code.includes('(A1)') && code.includes('(B1)') && code.includes('(C1)'))) {
      return { category: 'lang_tru_tam_giac' };
    }

    return { category: 'custom' };
  }, [tikzCode]);

  if (!parsedData) return null;

  // Render Bảng biến thiên trực quan
  const renderVariationTable = () => {
    const { xItems, signs, varNodes } = parsedData as {
      xItems: string[];
      signs: string[];
      varNodes: { type: string; val: string; val2?: string }[];
    };

    if (!xItems || xItems.length === 0) {
      return (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-800 text-xs">
          Bảng biến thiên: xem mã TikZ bên dưới
        </div>
      );
    }

    // Số cột cho các giá trị x
    const numCols = xItems.length;

    return (
      <div className="overflow-x-auto my-2 flex justify-center">
        <div className="inline-block border-2 border-slate-900 bg-white text-slate-900 font-sans text-xs">
          {/* Hàng 1: Giá trị của x */}
          <div className="flex border-b border-slate-900">
            <div className="w-14 shrink-0 p-1.5 font-bold border-r border-slate-900 flex items-center justify-center bg-slate-50">
              <MathView text="$x$" />
            </div>
            <div className="flex-1 flex justify-between px-3 py-1.5 items-center gap-6 min-w-[240px]">
              {xItems.map((val, idx) => (
                <div key={idx} className="font-medium text-center">
                  <MathView text={`$${val}$`} />
                </div>
              ))}
            </div>
          </div>

          {/* Hàng 2: Dấu của y' */}
          <div className="flex border-b border-slate-900">
            <div className="w-14 shrink-0 p-1 font-bold border-r border-slate-900 flex items-center justify-center bg-slate-50">
              <MathView text="$y'$" />
            </div>
            <div className="flex-1 flex justify-around px-2 py-1 items-center min-w-[240px]">
              {signs.map((s, idx) => {
                if (s === 'd') {
                  return (
                    <span key={idx} className="font-bold text-slate-900 px-1 border-x border-slate-900 mx-1">
                      ||
                    </span>
                  );
                }
                return (
                  <span key={idx} className="font-bold text-slate-900">
                    {s === '+' ? '+' : s === '-' ? '−' : s === '0' ? '0' : s}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Hàng 3: Chiều biến thiên của y với mũi tên SVG */}
          <div className="flex">
            <div className="w-14 shrink-0 p-2 font-bold border-r border-slate-900 flex items-center justify-center bg-slate-50">
              <MathView text="$y$" />
            </div>
            <div className="flex-1 p-2 relative h-24 min-w-[260px] flex items-center justify-between px-4">
              {/* Dựng đồ họa các đỉnh/đáy và mũi tên */}
              {varNodes && varNodes.length > 0 ? (
                <div className="w-full h-full flex justify-between items-center relative">
                  {varNodes.map((node, idx) => {
                    if (node.type === 'double_bar') {
                      return (
                        <div key={idx} className="flex flex-col items-center justify-between h-full py-1">
                          <span className="text-[11px] font-medium text-slate-800">
                            <MathView text={`$${node.val}$`} />
                          </span>
                          <div className="w-1 h-12 border-x border-slate-900 mx-2" />
                          <span className="text-[11px] font-medium text-slate-800">
                            <MathView text={`$${node.val2 || node.val}$`} />
                          </span>
                        </div>
                      );
                    }

                    const isUp = node.type === 'up';
                    return (
                      <div
                        key={idx}
                        className={`flex flex-col items-center ${
                          isUp ? 'self-start pt-1' : 'self-end pb-1'
                        }`}
                      >
                        <span className="text-[11px] font-bold text-slate-900">
                          <MathView text={`$${node.val}$`} />
                        </span>
                      </div>
                    );
                  })}
                  {/* SVG vẽ các mũi tên nối giữa các điểm */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
                    <defs>
                      <marker
                        id="arrow"
                        viewBox="0 0 10 10"
                        refX="5"
                        refY="5"
                        markerWidth="5"
                        markerHeight="5"
                        orient="auto-start-reverse"
                      >
                        <path d="M 0 1 L 9 5 L 0 9 z" fill="#0f172a" />
                      </marker>
                    </defs>
                    {varNodes.map((node, i) => {
                      if (i === varNodes.length - 1) return null;
                      const next = varNodes[i + 1];
                      if (node.type === 'double_bar' || next.type === 'double_bar') return null;

                      // Tính tọa độ phần trăm
                      const x1 = (i / (varNodes.length - 1)) * 100 + 4;
                      const x2 = ((i + 1) / (varNodes.length - 1)) * 100 - 4;
                      const y1 = node.type === 'up' ? 22 : 78;
                      const y2 = next.type === 'up' ? 22 : 78;

                      return (
                        <line
                          key={i}
                          x1={`${x1}%`}
                          y1={`${y1}%`}
                          x2={`${x2}%`}
                          y2={`${y2}%`}
                          stroke="#0f172a"
                          strokeWidth="1.5"
                          markerEnd="url(#arrow)"
                        />
                      );
                    })}
                  </svg>
                </div>
              ) : (
                <div className="w-full text-center text-slate-400 italic text-xs">
                  (Đồ thị biến thiên)
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render Hình chóp tam giác S.ABC
  const renderChopTamGiac = () => (
    <div className="flex justify-center my-2">
      <svg
        viewBox="0 0 240 180"
        className="w-48 h-36 bg-white border border-slate-200 rounded p-1 text-slate-900"
      >
        {/* Nét đứt (cạnh khuất) */}
        <line x1="80" y1="110" x2="30" y2="150" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />
        <line x1="80" y1="110" x2="200" y2="140" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />
        <line x1="80" y1="25" x2="80" y2="110" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />

        {/* Nét liền (cạnh nhìn thấy) */}
        <line x1="80" y1="25" x2="30" y2="150" stroke="#000" strokeWidth="1.5" />
        <line x1="80" y1="25" x2="200" y2="140" stroke="#000" strokeWidth="1.5" />
        <line x1="30" y1="150" x2="200" y2="140" stroke="#000" strokeWidth="1.5" />

        {/* Ký hiệu góc vuông tại A */}
        <path d="M 80 98 L 92 101 L 92 113" fill="none" stroke="#000" strokeWidth="1.2" />

        {/* Các đỉnh và nhãn */}
        <circle cx="80" cy="25" r="2.5" fill="#000" />
        <text x="80" y="18" textAnchor="middle" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">S</text>

        <circle cx="80" cy="110" r="2.5" fill="#000" />
        <text x="70" y="112" textAnchor="end" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">A</text>

        <circle cx="30" cy="150" r="2.5" fill="#000" />
        <text x="22" y="160" textAnchor="end" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">B</text>

        <circle cx="200" cy="140" r="2.5" fill="#000" />
        <text x="210" y="145" textAnchor="start" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">C</text>
      </svg>
    </div>
  );

  // Render Hình chóp tứ giác S.ABCD
  const renderChopTuGiac = () => (
    <div className="flex justify-center my-2">
      <svg
        viewBox="0 0 250 190"
        className="w-52 h-40 bg-white border border-slate-200 rounded p-1 text-slate-900"
      >
        {/* Nét đứt (cạnh khuất) */}
        <line x1="75" y1="110" x2="30" y2="155" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />
        <line x1="75" y1="110" x2="210" y2="110" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />
        <line x1="75" y1="25" x2="75" y2="110" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />

        {/* Nét liền (cạnh nhìn thấy) */}
        <line x1="30" y1="155" x2="165" y2="155" stroke="#000" strokeWidth="1.5" />
        <line x1="165" y1="155" x2="210" y2="110" stroke="#000" strokeWidth="1.5" />
        <line x1="75" y1="25" x2="30" y2="155" stroke="#000" strokeWidth="1.5" />
        <line x1="75" y1="25" x2="165" y2="155" stroke="#000" strokeWidth="1.5" />
        <line x1="75" y1="25" x2="210" y2="110" stroke="#000" strokeWidth="1.5" />

        {/* Ký hiệu góc vuông tại A */}
        <path d="M 75 98 L 87 98 L 87 110" fill="none" stroke="#000" strokeWidth="1.2" />

        {/* Các đỉnh và nhãn */}
        <circle cx="75" cy="25" r="2.5" fill="#000" />
        <text x="75" y="18" textAnchor="middle" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">S</text>

        <circle cx="75" cy="110" r="2.5" fill="#000" />
        <text x="65" y="112" textAnchor="end" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">A</text>

        <circle cx="30" cy="155" r="2.5" fill="#000" />
        <text x="22" y="165" textAnchor="end" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">B</text>

        <circle cx="165" cy="155" r="2.5" fill="#000" />
        <text x="175" y="168" textAnchor="start" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">C</text>

        <circle cx="210" cy="110" r="2.5" fill="#000" />
        <text x="220" y="112" textAnchor="start" fontSize="13" fontWeight="bold" fontFamily="Times New Roman">D</text>
      </svg>
    </div>
  );

  // Render Hình lăng trụ tam giác ABC.A'B'C'
  const renderLangTru = () => (
    <div className="flex justify-center my-2">
      <svg
        viewBox="0 0 240 190"
        className="w-48 h-38 bg-white border border-slate-200 rounded p-1 text-slate-900"
      >
        {/* Nét đứt (cạnh đáy dưới khuất) */}
        <line x1="75" y1="130" x2="30" y2="160" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />
        <line x1="75" y1="130" x2="190" y2="145" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />
        <line x1="75" y1="40" x2="75" y2="130" stroke="#000" strokeWidth="1.5" strokeDasharray="4,4" />

        {/* Nét liền */}
        <line x1="30" y1="160" x2="190" y2="145" stroke="#000" strokeWidth="1.5" />
        <line x1="75" y1="40" x2="30" y2="70" stroke="#000" strokeWidth="1.5" />
        <line x1="75" y1="40" x2="190" y2="55" stroke="#000" strokeWidth="1.5" />
        <line x1="30" y1="70" x2="190" y2="55" stroke="#000" strokeWidth="1.5" />
        <line x1="30" y1="70" x2="30" y2="160" stroke="#000" strokeWidth="1.5" />
        <line x1="190" y1="55" x2="190" y2="145" stroke="#000" strokeWidth="1.5" />

        {/* Nhãn */}
        <text x="65" y="38" textAnchor="end" fontSize="12" fontWeight="bold" fontFamily="Times New Roman">A'</text>
        <text x="20" y="70" textAnchor="end" fontSize="12" fontWeight="bold" fontFamily="Times New Roman">B'</text>
        <text x="200" y="58" textAnchor="start" fontSize="12" fontWeight="bold" fontFamily="Times New Roman">C'</text>

        <text x="65" y="132" textAnchor="end" fontSize="12" fontWeight="bold" fontFamily="Times New Roman">A</text>
        <text x="20" y="165" textAnchor="end" fontSize="12" fontWeight="bold" fontFamily="Times New Roman">B</text>
        <text x="200" y="150" textAnchor="start" fontSize="12" fontWeight="bold" fontFamily="Times New Roman">C</text>
      </svg>
    </div>
  );

  // Nếu đang ở chế độ in A4: chỉ render hình trực quan, không hiển thị thanh công cụ
  if (printMode) {
    return (
      <div className={`my-2 text-center ${className}`}>
        {parsedData.category === 'table' && renderVariationTable()}
        {parsedData.category === 'chop_tam_giac' && renderChopTamGiac()}
        {parsedData.category === 'chop_tu_giac' && renderChopTuGiac()}
        {parsedData.category === 'lang_tru_tam_giac' && renderLangTru()}
        {parsedData.category === 'custom' && (
          <div className="p-2 border border-slate-300 rounded text-xs italic text-slate-500">
            [Đồ thị / Hình vẽ TikZ]
          </div>
        )}
      </div>
    );
  }

  // Chế độ Visual Editor (Màn hình biên tập của giáo viên)
  return (
    <div className={`my-3 p-3 bg-slate-50 border border-slate-200 rounded-xl ${className}`}>
      {/* Thanh công cụ xem trước / chuyển mã */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-xs font-bold text-slate-700">
            {parsedData.category === 'table'
              ? 'Bảng biến thiên trực quan'
              : parsedData.category.includes('chop') || parsedData.category.includes('lang_tru')
              ? 'Hình vẽ không gian trực quan'
              : 'Đồ thị / Hình vẽ TikZ'}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setShowRaw(!showRaw)}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shadow-xs transition-colors"
          >
            {showRaw ? <Eye className="w-3.5 h-3.5 text-blue-600" /> : <Code className="w-3.5 h-3.5 text-slate-600" />}
            <span>{showRaw ? 'Xem hình vẽ' : 'Sửa mã TikZ'}</span>
          </button>

          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shadow-xs transition-colors"
            title="Sao chép mã TikZ"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-600" />}
          </button>
        </div>
      </div>

      {/* Hiển thị hình trực quan hoặc mã nguồn TikZ */}
      {showRaw ? (
        <pre className="p-3 bg-slate-900 text-emerald-300 text-xs rounded-lg overflow-x-auto font-mono max-h-60">
          {tikzCode}
        </pre>
      ) : (
        <div>
          {parsedData.category === 'table' && renderVariationTable()}
          {parsedData.category === 'chop_tam_giac' && renderChopTamGiac()}
          {parsedData.category === 'chop_tu_giac' && renderChopTuGiac()}
          {parsedData.category === 'lang_tru_tam_giac' && renderLangTru()}
          {parsedData.category === 'custom' && (
            <div className="text-center py-4 bg-white rounded border border-dashed border-slate-300 text-xs text-slate-500">
              Đồ thị TikZ tùy biến: Bấm <strong>"Sửa mã TikZ"</strong> để xem code nguồn LaTeX.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
