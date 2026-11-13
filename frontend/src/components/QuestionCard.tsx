import React, { useRef, useState } from 'react';
import { MathView } from './MathView';
import { TikZView } from './TikZView';
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
  template_id?: string | null;
}

interface QuestionCardProps {
  question: Question;
  index: number;
  onRegenerate: (customPrompt?: string) => Promise<void>;
  onCloneNumbers: () => Promise<void>;
  onUpdate: (updatedQuestion: Question) => void;
  isActive?: boolean;
}

export const LEVEL_BADGES = {
  NHAN_BIET: { label: "NB", full: "Nhận biết", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  THONG_HIEU: { label: "TH", full: "Thông hiểu", color: "bg-blue-50 text-blue-700 border-blue-200" },
  VAN_DUNG: { label: "VD", full: "Vận dụng", color: "bg-amber-50 text-amber-700 border-amber-200" },
  VAN_DUNG_CAO: { label: "VDC", full: "Vận dụng cao", color: "bg-rose-50 text-rose-700 border-rose-200" }
} as const;

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
  const [numberEdit, setNumberEdit] = useState<{ start: number; end: number; value: string; top: number; left: number; width: number } | null>(null);
  const stemRef = useRef<HTMLDivElement>(null);
  const [inlineField, setInlineField] = useState<string | null>(null);
  const [draft, setDraft] = useState(question);
  const activeField = useRef<{ input: HTMLTextAreaElement; update: (value: string) => void } | null>(null);
  const [promptOpen, setPromptOpen] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  const levelBadges = LEVEL_BADGES;

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

  const insertMathSnippet = (snippet: (selection: string) => string) => {
    const field = activeField.current;
    if (!field) return;
    const { input, update } = field;
    const { value, selectionStart: start, selectionEnd: end } = input;
    const before = value.slice(0, start);
    const insideMath = (before.match(/(?<!\\)\$\$|(?<!\\)\$/g)?.length ?? 0) % 2 === 1;
    const formula = snippet(value.slice(start, end) || 'x');
    const insertion = insideMath ? formula : '$' + formula + '$';
    update(before + insertion + value.slice(end));
    input.focus();
    requestAnimationFrame(() => input.setSelectionRange(start + insertion.length, start + insertion.length));
  };

  const openEditor = () => {
    if (isRegenerating || isCloning) return;
    setNumberEdit(null);
    setDraft(question);
    setInlineField(null);
    setPromptOpen(false);
    setIsCodeEditing(true);
  };

  const editField = (label: string, value: string, update: (value: string) => void, rows = 2) => (
    <label className="block text-xs font-semibold text-slate-700">
      {label}
      <textarea
        rows={rows}
        value={value}
        onFocus={event => { activeField.current = { input: event.currentTarget, update }; }}
        onChange={event => update(event.target.value)}
        className="mt-1 block w-full resize-y rounded-md border border-slate-300 bg-white p-2 font-mono text-sm font-normal"
      />
    </label>
  );

  const renderInline = (label: string, text: string, patch: (value: string) => Partial<Question>,
    rendered = <MathView text={text} />, allowEmpty = false) => {
    if (inlineField === label) {
      return <textarea key={label} autoFocus aria-label={label} defaultValue={text}
        rows={Math.max(1, Math.ceil(text.length / 75), text.split('\n').length)}
        onFocus={event => {
          const input = event.currentTarget;
          input.setSelectionRange(input.value.length, input.value.length);
        }}
        onKeyDown={event => {
          if (event.key === 'Escape') {
            event.preventDefault();
            event.currentTarget.value = text;
            event.currentTarget.blur();
          } else if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            event.currentTarget.blur();
          }
        }}
        onBlur={event => {
          const value = event.currentTarget.value;
          setInlineField(null);
          if (value !== text && (allowEmpty || value.trim())) {
            onUpdate({ ...question, ...patch(value), verified: false, sympy_code: undefined, template_id: null });
          }
        }}
        className="block w-full resize-y rounded border border-blue-400 bg-white px-1 font-inherit leading-relaxed outline-none"
      />;
    }
    return <div tabIndex={0} aria-label={label} className="cursor-text rounded-sm hover:bg-blue-50/60 focus-visible:outline-blue-400"
      onDoubleClick={event => {
        if (numberEdit || isCodeEditing || isRegenerating || isCloning || (event.target as Element).closest('.editable-math-number, input')) return;
        setNumberEdit(null);
        setInlineField(label);
      }}
      onKeyDown={event => {
        if (event.key === 'F2' && !isCodeEditing && !isRegenerating && !isCloning) {
          event.preventDefault();
          setNumberEdit(null);
          setInlineField(label);
        }
      }}>
      {rendered}
    </div>;
  };

  const canSave = !!draft.stem.trim()
    && (draft.type !== 'MULTIPLE_CHOICE' || (draft.choices?.length === 4 &&
      draft.choices.every(choice => choice.trim()) && [0, 1, 2, 3].includes(draft.correct_index ?? -1)))
    && (draft.type !== 'TRUE_FALSE' || (draft.statements?.length === 4 &&
      draft.statements.every(item => item.statement.trim())))
    && (draft.type !== 'SHORT_ANSWER' || !!draft.correct_value?.trim());

  const handleSaveCodeEdit = () => {
    if (!canSave) return;
    if (draft !== question) {
      onUpdate({ ...draft, verified: false, sympy_code: undefined, template_id: null });
    }
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
              Chưa xác minh
            </span>
          )}
        </div>
      </div>

      {/* Micro-interactions Toolbar */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3 py-1.5 px-2 bg-slate-50/80 rounded-lg border border-slate-100 text-xs">
        {/* Đổi câu khác */}
        <button
          onClick={() => setPromptOpen(!promptOpen)}
          disabled={isRegenerating || isCloning || isCodeEditing || !!numberEdit || !!inlineField}
          className="inline-flex items-center gap-1 text-violet-700 hover:text-violet-900 bg-violet-50 hover:bg-violet-100 font-semibold px-2.5 py-1 rounded transition-colors duration-150 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
          <span>Đổi câu khác</span>
        </button>

        {/* Đổi số liệu */}
        <button
          onClick={handleCloneClick}
          disabled={isRegenerating || isCloning || isCodeEditing || !!numberEdit || !!inlineField}
          className="inline-flex items-center gap-1 text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 font-semibold px-2.5 py-1 rounded transition-colors duration-150 disabled:opacity-50"
        >
          <Hash className={`w-3.5 h-3.5 ${isCloning ? 'animate-spin' : ''}`} />
          <span>Đổi số liệu</span>
        </button>

        {/* Sửa LaTeX trực tiếp */}
        <button
          disabled={isRegenerating || isCloning}
          onClick={() => isCodeEditing ? setIsCodeEditing(false) : openEditor()}
          className={`inline-flex items-center gap-1 font-semibold px-2.5 py-1 rounded transition-colors duration-150 ${
            isCodeEditing 
              ? "bg-slate-800 text-white" 
              : "text-slate-700 hover:text-slate-900 bg-white border border-slate-200"
          }`}
        >
          <Code className="w-3.5 h-3.5" />
          <span>{isCodeEditing ? 'Đóng trình sửa' : 'Sửa nội dung'}</span>
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

      {isCodeEditing ? (
        <div className="mb-4 space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="flex flex-wrap gap-2">
            {([
              ['Căn bậc hai', (x: string) => `\\sqrt{${x}}`],
              ['Căn bậc n', (x: string) => `\\sqrt[n]{${x}}`],
              ['Phân số', (x: string) => `\\frac{${x}}{b}`],
              ['Số mũ', (x: string) => `{${x}}^{2}`],
            ] as const).map(([label, snippet]) => (
              <button key={label} type="button"
                onMouseDown={event => event.preventDefault()}
                onClick={() => insertMathSnippet(snippet)}
                className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-medium">
                {label}
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-600">Đặt con trỏ hoặc bôi đen nội dung để chèn công thức. Kiểm tra lại đáp án và lời giải nếu đổi dữ kiện.</p>
          {editField('Đề bài', draft.stem, stem => setDraft(prev => ({ ...prev, stem })), 4)}
          <div className="rounded border border-slate-200 bg-white p-2 text-sm">
            <div className="mb-1 text-xs font-semibold text-slate-600">Xem trước đề bài</div>
            <MathView text={draft.stem} />
          </div>

          {draft.type === 'MULTIPLE_CHOICE' && (
            <>
              {Array.from({ length: 4 }, (_, i) => editField(
                'Phương án ' + 'ABCD'[i], draft.choices?.[i] ?? '',
                value => setDraft(prev => ({
                  ...prev, choices: Array.from({ length: 4 }, (_, index) =>
                    index === i ? value : prev.choices?.[index] ?? ''),
                })),
              )).map((field, i) => <React.Fragment key={i}>{field}</React.Fragment>)}
              <label className="block text-xs font-semibold">
                Đáp án đúng
                <select className="ml-2 rounded border bg-white p-1" value={draft.correct_index ?? ''}
                  onChange={event => {
                    const value = event.target.value;
                    setDraft(prev => ({ ...prev, correct_index: value === '' ? undefined : Number(value) }));
                  }}>
                  <option value="">Chọn đáp án</option>
                  {[0, 1, 2, 3].map(i => <option key={i} value={i}>{'ABCD'[i]}</option>)}
                </select>
              </label>
            </>
          )}

          {draft.type === 'TRUE_FALSE' && draft.statements?.map((item, i) => {
            const updateItem = (values: Partial<TrueFalseItem>) => setDraft(prev => ({
              ...prev, statements: prev.statements?.map((statement, index) =>
                index === i ? { ...statement, ...values } : statement),
            }));
            return (
              <div key={i} className="space-y-2 border-t border-slate-200 pt-2">
                {editField('Mệnh đề ' + 'abcd'[i], item.statement, statement => updateItem({ statement }))}
                <label className="flex items-center gap-2 text-xs">
                  <input type="checkbox" checked={item.is_correct}
                    onChange={event => updateItem({ is_correct: event.target.checked })} />
                  Mệnh đề đúng
                </label>
                {editField('Giải thích', item.explanation ?? '', explanation => updateItem({ explanation }))}
              </div>
            );
          })}
          {draft.type === 'SHORT_ANSWER' && editField('Đáp số', draft.correct_value ?? '',
            correct_value => setDraft(prev => ({ ...prev, correct_value })), 1)}
          {editField('Lời giải', draft.solution, solution => setDraft(prev => ({ ...prev, solution })), 4)}
          <div className="flex justify-end gap-2">
            <button onClick={() => setIsCodeEditing(false)} className="rounded border px-3 py-1 text-xs">Hủy</button>
            <button onClick={handleSaveCodeEdit} disabled={!canSave}
              className="inline-flex items-center gap-1 rounded bg-blue-600 px-3 py-1 text-xs font-bold text-white disabled:opacity-50">
              <Check className="w-3.5 h-3.5" /> Lưu thay đổi
            </button>
          </div>
        </div>
      ) : (
        <div ref={stemRef} className="relative mb-4 text-sm font-normal leading-relaxed text-slate-900 md:text-base">
          {renderInline('Đề bài', question.stem, stem => ({ stem }), <MathView text={question.stem} onNumberEdit={isRegenerating || isCloning ? undefined : (start, end, value, target) => {
            const bounds = stemRef.current?.getBoundingClientRect();
            if (!bounds) return;
            const number = target.getBoundingClientRect();
            setNumberEdit({
              start, end, value, top: number.top - bounds.top + number.height / 2,
              left: number.left - bounds.left, width: Math.max(number.width + 10, 26),
            });
          }} />)}
          {numberEdit && (
            <input
              key={numberEdit.start}
              autoFocus
              aria-label="Sửa nội dung tại vị trí đã chọn"
              inputMode={/^\d/.test(numberEdit.value) ? "decimal" : "text"}
              defaultValue={numberEdit.value.replace('{,}', ',')}
              onFocus={event => event.currentTarget.select()}
              onInput={event => {
                const input = event.currentTarget;
                input.style.width = Math.max(numberEdit.width, input.value.length * 10 + 10) + 'px';
              }}
              onKeyDown={event => {
                if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
                  event.preventDefault();
                  event.currentTarget.blur();
                }
                if (event.key === 'Escape') {
                  event.currentTarget.value = numberEdit.value.replace('{,}', ',');
                  event.currentTarget.blur();
                }
              }}
              onBlur={event => {
                const value = event.currentTarget.value.trim();
                setNumberEdit(null);
                if (!value || value === numberEdit.value.replace('{,}', ',')) return;
                const stem = question.stem.normalize('NFC');
                if (stem.slice(numberEdit.start, numberEdit.end) !== numberEdit.value) return;
                const prefix = stem.slice(0, numberEdit.start);
                let replacement = numberEdit.value.includes('{,}') ? value.replaceAll(',', '{,}') : value;
                if (/[_^]$/.test(prefix) && replacement.length > 1) replacement = '{' + replacement + '}';
                onUpdate({ ...question, stem: prefix + replacement + stem.slice(numberEdit.end),
                  verified: false, sympy_code: undefined, template_id: null });
              }}
              className="absolute z-10 -translate-y-1/2 rounded-sm border border-blue-500 bg-white px-1 text-center leading-tight text-slate-900 outline-none"
              style={{ top: numberEdit.top, left: numberEdit.left, width: numberEdit.width }}
            />
          )}
        </div>
      )}

      {/* Hiển thị TikZ / tkz-tab trực quan */}
      {question.tikz_code && (
        <TikZView tikzCode={question.tikz_code} />
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
                <div className="min-w-0 flex-1 overflow-x-auto py-1">
                  {renderInline('Phương án ' + letters[i], choice, value => ({
                    choices: question.choices?.map((option, index) => index === i ? value : option),
                  }))}
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
                    {renderInline('Mệnh đề ' + labels[i], st.statement, value => ({
                      statements: question.statements?.map((item, index) =>
                        index === i ? { ...item, statement: value } : item),
                    }))}
                    {st.explanation && (
                      <div className="mt-0.5 text-xs italic text-slate-500">
                        {renderInline('Giải thích ' + labels[i], st.explanation, value => ({
                          statements: question.statements?.map((item, index) =>
                            index === i ? { ...item, explanation: value } : item),
                        }), undefined, true)}
                      </div>
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
          <div className="min-w-24 rounded-md border border-blue-300 bg-white px-2 py-1 font-mono text-blue-700">
            {renderInline('Đáp số', question.correct_value ?? '', correct_value => ({ correct_value }),
              <span>{question.correct_value || 'Chưa có'}</span>)}
          </div>
        </div>
      )}

      {question.type === "ESSAY" && (
        <div className="mb-4 p-3 bg-indigo-50/70 rounded-lg border border-indigo-200 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-600" />
            <span className="text-xs font-bold text-indigo-900 uppercase">Hình thức: Câu hỏi Tự luận</span>
          </div>
          <span className="text-xs text-indigo-700 italic">Học sinh trình bày lời giải và lập luận chi tiết</span>
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
            <span>Lời giải</span>
          </span>
          {showSolution ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showSolution && (
          <div className="mt-2 p-3.5 bg-amber-50/60 rounded-lg border border-amber-200 text-sm text-slate-800 leading-relaxed font-normal">
            {renderInline('Lời giải', question.solution, solution => ({ solution }), undefined, true)}
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
