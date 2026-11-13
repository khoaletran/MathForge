import React, { useState } from 'react';
import { 
  Download, Copy, Check, FileText, X, Printer, 
  Terminal, Loader2, Shuffle, CheckSquare, Layers 
} from 'lucide-react';
import { Question } from './QuestionCard';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  latexCode: string;
  onCompilePdf: () => Promise<void>;
  isCompiling: boolean;
  includeSolution: boolean;
  onToggleSolution: (val: boolean) => void;
  examMeta: {
    school_name: string;
    exam_name: string;
    academic_year: string;
    exam_code: string;
  };
  onUpdateExamMeta: (meta: any) => void;
  questions: Question[];
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  latexCode,
  onCompilePdf,
  isCompiling,
  includeSolution,
  onToggleSolution,
  examMeta,
  onUpdateExamMeta,
  questions
}) => {
  const [copied, setCopied] = useState(false);
  const [shuffleCodes, setShuffleCodes] = useState<string[]>(['101', '102', '103', '104']);
  const [selectedNumCodes, setSelectedNumCodes] = useState<number>(1);
  const [isShuffling, setIsShuffling] = useState(false);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(latexCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTex = () => {
    const element = document.createElement("a");
    const file = new Blob([latexCode], { type: 'text/plain;charset=utf-8' });
    element.href = URL.createObjectURL(file);
    element.download = `De_thi_Toan_${examMeta.exam_code}.tex`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleShuffleGenerate = async () => {
    setIsShuffling(true);
    try {
      const activeCodes = shuffleCodes.slice(0, selectedNumCodes);
      const res = await fetch('/api/generate/shuffle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper: {
            id: `exam_${examMeta.exam_code}`,
            title: examMeta.exam_name,
            school_name: examMeta.school_name,
            exam_name: examMeta.exam_name,
            academic_year: examMeta.academic_year,
            exam_code: examMeta.exam_code,
            time_minutes: 90,
            questions: questions
          },
          codes: activeCodes
        })
      });

      if (res.ok) {
        alert(`Đã trộn thành công ${activeCodes.length} mã đề (${activeCodes.join(', ')})!`);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsShuffling(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overscroll-contain"
      role="dialog"
      aria-modal="true"
      aria-labelledby="export-dialog-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <h3 id="export-dialog-title" className="font-bold text-slate-900 text-lg">Xuất Bản & Trộn Mã Đề Thi</h3>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Đóng cửa sổ xuất bản"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Header Metadata Config */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wide block">
              Thông tin tiêu đề đề thi (LaTeX Header Macro)
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="text-slate-500 block mb-1">Sở / Trường:</label>
                <input
                  type="text"
                  value={examMeta.school_name}
                  onChange={(e) => onUpdateExamMeta({ ...examMeta, school_name: e.target.value })}
                  className="w-full p-2 bg-white border border-slate-300 rounded-md font-medium"
                />
              </div>
              <div>
                <label className="text-slate-500 block mb-1">Tên kỳ thi:</label>
                <input
                  type="text"
                  value={examMeta.exam_name}
                  onChange={(e) => onUpdateExamMeta({ ...examMeta, exam_name: e.target.value })}
                  className="w-full p-2 bg-white border border-slate-300 rounded-md font-medium"
                />
              </div>
              <div>
                <label className="text-slate-500 block mb-1">Năm học:</label>
                <input
                  type="text"
                  value={examMeta.academic_year}
                  onChange={(e) => onUpdateExamMeta({ ...examMeta, academic_year: e.target.value })}
                  className="w-full p-2 bg-white border border-slate-300 rounded-md font-medium"
                />
              </div>
              <div>
                <label className="text-slate-500 block mb-1">Mã đề gốc:</label>
                <input
                  type="text"
                  value={examMeta.exam_code}
                  onChange={(e) => onUpdateExamMeta({ ...examMeta, exam_code: e.target.value })}
                  className="w-full p-2 bg-white border border-slate-300 rounded-md font-medium font-mono"
                />
              </div>
            </div>
          </div>

          {/* Exam Shuffler Options */}
          <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-900 uppercase tracking-wide flex items-center gap-1.5">
                <Shuffle className="w-4 h-4 text-blue-600" />
                Trộn Mã Đề Thi Tự Động (Exam Shuffler)
              </span>
              <span className="text-xs text-blue-700">
                Quy tắc: Giữ nguyên các phần, hoán vị các phương án A, B, C, D
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs text-slate-700 font-medium">Số lượng mã đề cần tạo:</span>
              {[1, 2, 4].map(n => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setSelectedNumCodes(n)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                    selectedNumCodes === n
                      ? "bg-blue-600 text-white shadow-xs"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {n} mã đề ({shuffleCodes.slice(0, n).join(', ')})
                </button>
              ))}

              {selectedNumCodes > 1 && (
                <button
                  type="button"
                  onClick={handleShuffleGenerate}
                  disabled={isShuffling}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition disabled:opacity-50"
                >
                  <Shuffle className="w-3.5 h-3.5" />
                  <span>{isShuffling ? 'Đang trộn...' : 'Bắt đầu trộn đề'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Option kèm lời giải */}
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer font-medium">
            <input
              type="checkbox"
              checked={includeSolution}
              onChange={(e) => onToggleSolution(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
            />
            <span>Bao gồm lời giải chi tiết và bảng tra cứu đáp án ở cuối đề</span>
          </label>

          {/* Code Viewer Preview */}
          <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-mono text-emerald-400">Mã nguồn LaTeX ex_test.sty (UTF-8):</span>
              <button
                type="button"
                onClick={handleCopy}
                className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-semibold text-xs"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Đã sao chép' : 'Sao chép mã'}</span>
              </button>
            </div>

            <textarea
              readOnly
              value={latexCode}
              className="w-full h-44 bg-slate-900 text-emerald-300 font-mono text-xs p-3 rounded-lg border border-slate-800 focus:outline-none resize-none overflow-y-auto leading-relaxed select-all"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs text-slate-500 hidden sm:inline">
            Tương thích 100% với <strong>Overleaf</strong>, <strong>TeXstudio</strong>, <strong>VS Code</strong>.
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadTex}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold rounded-lg border border-slate-200 transition"
            >
              <Download className="w-4 h-4 text-blue-600" />
              <span>Tải file .tex</span>
            </button>

            <button
              onClick={onCompilePdf}
              disabled={isCompiling}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {isCompiling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang biên dịch PDF...</span>
                </>
              ) : (
                <>
                  <Printer className="w-4 h-4" />
                  <span>Biên dịch PDF (TeX Live)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
