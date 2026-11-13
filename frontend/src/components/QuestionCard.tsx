import React, { useState } from 'react';
import { MathView } from './MathView';
import { 
  RefreshCw, CheckCircle2, ChevronDown, ChevronUp, 
  Code, ShieldCheck, Sparkles, Hash, ArrowUpRight, 
  Check, X, FileEdit 
} from 'lucide-react';

export interface TrueFalseItem {
  statement: string;
  is_correct: boolean;
  explanation?: string;
}

export interface Question {
  id: string;
  type: "MULTIPLE_CHOICE" | "TRUE_FALSE" | "SHORT_ANSWER" | "ESSAY";
  topic: string;
  subtopic?: string;
  level: "NHAN_BIET" | "THONG_HIEU" | "VAN_DUNG" | "VAN_DUNG_CAO";
  stem: string;
  choices?: string[];
  correct_index?: number;
  statements?: TrueFalseItem[];
  correct_value?: string;
  solution: string;
  tikz_code?: string;
  sympy_code?: string;
  verified?: boolean;
}

interface QuestionCardProps {
  question: Question;
  index: number;
  onRegenerate: (customPrompt?: string) => Promise<void>;
  onCloneNumbers: () => Promise<void>;
  onUpdate: (updatedQuestion: Question) => void;
  isActive?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  index,
  onRegenerate,
  onCloneNumbers,
  onUpdate,
  isActive = false
}) => {
  const [showSolution, setShowSolution] = useState(false);
  const [showTikz, setShowTikz] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isCloning, setIsCloning] = useState(false);
  const [isCodeEditing, setIsCodeEditing] = useState(false);
  const [editStem, setEditStem] = useState(question.stem);
  const [promptOpen, setPromptOpen] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  // Màu sắc chuẩn UX thiết kế
  const levelBadges = {
    NHAN_BIET: { label: "NB", full: "Nhận biết", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    THONG_HIEU: { label: "TH", full: "Thông hiểu", color: "bg-blue-50 text-blue-700 border-blue-200" },
    VAN_DUNG: { label: "VD", full: "Vận dụng", color: "bg-amber-50 text-amber-700 border-amber-200" },
    VAN_DUNG_CAO: { label: "VDC", full: "Vận dụng cao", color: "bg-rose-50 text-rose-700 border-rose-200" }
  };

  const handleRegenerateClick = async () => {
    setIsRegenerating(true);
    try {
      await onRegenerate(customPrompt ? customPrompt : undefined);
      setCustomPrompt('');
      setPromptOpen(false);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleCloneClick = async () => {
    setIsCloning(true);
    try {
      await onCloneNumbers();
    } finally {
      setIsCloning(false);
    }
  };

  const insertMathSnippet = (snippet: string) => {
    setEditStem(prev => prev + snippet);
  };

  const handleSaveCodeEdit = () => {
    onUpdate({
      ...question,
      stem: editStem
    });
    setIsCodeEditing(false);
  };

  return (
    <div 
      id={`question-card-${index}`}
      className={`bg-white rounded-xl border transition-[border-color,box-shadow] duration-150 p-5 mb-4 scroll-mt-24 ${
        isActive 
          ? "border-blue-500 ring-2 ring-blue-100 shadow-md" 
          : "border-slate-200 shadow-xs hover:border-slate-300 hover:shadow-sm"
      }`}
    >
      {/* Top Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="font-extrabold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-md text-xs md:text-sm">
            Câu {index + 1}
          </span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full border font-bold ${levelBadges[question.level]?.color || ''}`}>
            {levelBadges[question.level]?.label} • {levelBadges[question.level]?.full}
          </span>
          <span className="text-xs text-slate-500 font-medium hidden sm:inline">
            {question.topic} {question.subtopic ? `• ${question.subtopic}` : ''}
          </span>
        </div>

        {/* SymPy Guardrail Badge */}
        <div className="flex items-center gap-2">
          {question.verified ? (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200" title="Đã qua kiểm chứng đại số máy tính SymPy">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="hidden md:inline">SymPy Verified</span>
            </span>
          ) : (
            <span className="text-[11px] text-slate-400 bg-slate-50 px-2 py-0.5 rounded-md">
              Chưa verify
            </span>
          )}
        </div>
      </div>

      {/* Micro-interactions Toolbar */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3 py-1.5 px-2 bg-slate-50/80 rounded-lg border border-slate-100 text-xs">
        {/* Đổi câu khác */}
        <button
          onClick={() => setPromptOpen(!promptOpen)}
          disabled={isRegenerating || isCloning}
          className="inline-flex items-center gap-1 text-violet-700 hover:text-violet-900 bg-violet-50 hover:bg-violet-100 font-semibold px-2.5 py-1 rounded transition-colors duration-150 disabled:opacity-50"
          title="Tạo bài toán khác cùng chủ đề và mức độ"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
          <span>Đổi câu khác</span>
        </button>

        {/* Đổi số liệu (Clone) */}
        <button
          onClick={handleCloneClick}
          disabled={isRegenerating || isCloning}
          className="inline-flex items-center gap-1 text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 font-semibold px-2.5 py-1 rounded transition-colors duration-150 disabled:opacity-50"
          title="Giữ nguyên dạng bài, chỉ đổi các tham số số liệu"
        >
          <Hash className={`w-3.5 h-3.5 ${isCloning ? 'animate-spin' : ''}`} />
          <span>Đổi số liệu (Clone)</span>
        </button>

        {/* Sửa LaTeX trực tiếp */}
        <button
          onClick={() => setIsCodeEditing(!isCodeEditing)}
          className={`inline-flex items-center gap-1 font-semibold px-2.5 py-1 rounded transition-colors duration-150 ${
            isCodeEditing 
              ? "bg-slate-800 text-white" 
              : "text-slate-700 hover:text-slate-900 bg-white border border-slate-200"
          }`}
          title="Bật trình sửa mã LaTeX trực tiếp cho câu này"
        >
          <Code className="w-3.5 h-3.5" />
          <span>{isCodeEditing ? 'Đóng Editor' : 'Sửa LaTeX'}</span>
        </button>
      </div>

      {/* Form tùy biến khi bấm Đổi câu khác */}
      {promptOpen && (
        <div className="mb-4 p-3 bg-violet-50/70 rounded-lg border border-violet-100 flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            aria-label="Yêu cầu cụ thể cho câu hỏi mới"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Yêu cầu cụ thể: 'cho đồ thị hàm bậc 3', 'nghiệm nguyên', 'cho số liệu lẻ'…"
            className="flex-1 text-xs bg-white border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
          />
          <button
            onClick={handleRegenerateClick}
            disabled={isRegenerating}
            className="inline-flex items-center justify-center gap-1 text-xs font-bold text-white bg-violet-600 hover:bg-violet-700 px-3.5 py-1.5 rounded-md transition-colors duration-150"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Sinh ngay
          </button>
        </div>
      )}

      {/* Trình sửa LaTeX câu hỏi (Mini Code Editor) */}
      {isCodeEditing ? (
        <div className="mb-4 p-3 bg-slate-900 rounded-xl border border-slate-800 text-slate-100 space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <span className="font-mono text-slate-400">Trình soạn LaTeX nhanh:</span>
            {/* Thanh công cụ chèn nhanh ký hiệu */}
            <div className="flex flex-wrap gap-1 font-mono text-[11px]">
              {[
                { label: '\\frac{}{}', code: '\\frac{a}{b}' },
                { label: '\\sqrt{}', code: '\\sqrt{x}' },
                { label: '\\int', code: '\\int_{a}^{b} f(x)dx' },
                { label: '\\vec{}', code: '\\overrightarrow{u}' },
                { label: '\\in \\mathbb{R}', code: '\\in \\mathbb{R}' },
              ].map(s => (
                <button
                  key={s.label}
                  type="button"
                  onClick={() => insertMathSnippet(s.code)}
                  className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <textarea
            aria-label="Mã nguồn LaTeX của đề bài"
            value={editStem}
            onChange={(e) => setEditStem(e.target.value)}
            className="w-full h-28 bg-slate-950 font-mono text-xs text-emerald-400 p-3 rounded-lg border border-slate-800 focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 leading-relaxed"
          />

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsCodeEditing(false)}
              className="px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md"
            >
              Hủy
            </button>
            <button
              onClick={handleSaveCodeEdit}
              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-md shadow-sm"
            >
              <Check className="w-3.5 h-3.5" /> Lưu thay đổi
            </button>
          </div>
        </div>
      ) : (
        /* Đề bài hiển thị KaTeX */
        <div className="text-slate-900 text-sm md:text-base mb-4 font-normal leading-relaxed">
          <MathView text={question.stem} />
        </div>
      )}

      {/* Hiển thị TikZ / tkz-tab nếu có */}
      {question.tikz_code && (
        <div className="mb-4">
          <button
            onClick={() => setShowTikz(!showTikz)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 px-2.5 py-1 rounded-md"
          >
            <Code className="w-3.5 h-3.5" />
            <span>Mã TikZ / tkz-tab ({showTikz ? 'Ẩn' : 'Xem mã nguồn'})</span>
          </button>
          {showTikz && (
            <pre className="mt-2 p-3 bg-slate-900 text-emerald-300 text-xs rounded-lg overflow-x-auto font-mono">
              {question.tikz_code}
            </pre>
          )}
        </div>
      )}

      {/* Phương án theo từng dạng câu */}
      {question.type === "MULTIPLE_CHOICE" && question.choices && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 mb-4">
          {question.choices.map((choice, i) => {
            const isCorrect = question.correct_index === i;
            const letters = ["A", "B", "C", "D"];
            return (
              <div
                key={i}
                className={`flex items-start gap-2.5 p-3 rounded-lg border text-sm transition-all ${
                  isCorrect
                    ? "bg-emerald-50/80 border-emerald-300 text-emerald-950 font-medium"
                    : "bg-slate-50/60 border-slate-200 text-slate-800"
                }`}
              >
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                  isCorrect ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-700"
                }`}>
                  {letters[i]}
                </span>
                <div className="flex-1 overflow-x-auto pt-0.5">
                  <MathView text={choice} />
                </div>
                {isCorrect && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 ml-1 mt-0.5" />
                )}
              </div>
            );
          })}
        </div>
      )}

      {question.type === "TRUE_FALSE" && question.statements && (
        <div className="space-y-2 mb-4">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
            Xét tính đúng hay sai của từng mệnh đề:
          </div>
          {question.statements.map((st, i) => {
            const labels = ["a", "b", "c", "d"];
            return (
              <div
                key={i}
                className={`p-3 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                  st.is_correct ? "bg-emerald-50/50 border-emerald-200" : "bg-rose-50/50 border-rose-200"
                }`}
              >
                <div className="flex items-start gap-2 flex-1">
                  <span className="font-bold text-xs uppercase px-1.5 py-0.5 bg-slate-200 text-slate-800 rounded">
                    {labels[i]}
                  </span>
                  <div className="text-sm">
                    <MathView text={st.statement} />
                    {st.explanation && (
                      <span className="text-xs text-slate-500 block mt-0.5 italic">
                        {st.explanation}
                      </span>
                    )}
                  </div>
                </div>
                <div className="shrink-0">
                  <span className={`inline-flex items-center gap-1 text-xs font-extrabold px-2.5 py-1 rounded-md ${
                    st.is_correct ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"
                  }`}>
                    {st.is_correct ? "ĐÚNG" : "SAI"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {question.type === "SHORT_ANSWER" && (
        <div className="mb-4 p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center gap-3">
          <span className="text-sm font-semibold text-slate-700">Đáp số cần điền:</span>
          <span className="font-mono font-bold text-base px-3 py-1 bg-white border-2 border-blue-600 text-blue-700 rounded-md shadow-xs">
            {question.correct_value || 'Chưa có'}
          </span>
        </div>
      )}

      {/* Lời giải chi tiết (Chain-of-Thought) */}
      <div className="pt-2 border-t border-slate-100">
        <button
          onClick={() => setShowSolution(!showSolution)}
          className="flex items-center justify-between w-full text-xs font-semibold text-slate-600 hover:text-slate-900 py-1"
        >
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-violet-600" />
            <span>Lời giải chi tiết (Chain-of-thought)</span>
          </span>
          {showSolution ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showSolution && (
          <div className="mt-2 p-3.5 bg-amber-50/60 rounded-lg border border-amber-200 text-sm text-slate-800 leading-relaxed font-normal">
            <MathView text={question.solution} />
            {question.sympy_code && (
              <div className="mt-3 pt-2 border-t border-amber-200">
                <span className="text-xs font-bold text-amber-900 block mb-1">Mã xác thực SymPy:</span>
                <pre className="text-xs font-mono bg-white p-2 rounded border border-amber-200 overflow-x-auto text-slate-700">
                  {question.sympy_code}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
