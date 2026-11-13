import React, { useState, useMemo, useLayoutEffect, useEffect, useRef, startTransition, ViewTransition } from 'react';
import { 
  Sparkles, FileText, CheckCircle2, RefreshCw, Printer, 
  Copy, Check, Code, Eye, FileDown, Layers, ChevronRight, 
  AlertCircle, ShieldCheck, Download, ExternalLink, SlidersHorizontal,
  Columns, Maximize2, Minimize2, Wand2, Loader2, CircleDashed, Cpu, FileCode2, Sigma
} from 'lucide-react';
import { QuestionCard, Question, LEVEL_BADGES } from './QuestionCard';
import { MathView } from './MathView';
import { TikZView } from './TikZView';
import { ExamMatrix } from './MatrixManager';

interface ExamStudioProps {
  onLayoutChange: (layout: { choice_layout: 'auto' | '4col' | '2col' | '1col'; density: 'compact' | 'normal' | 'spacious'; font_size: 'sm' | 'base' | 'lg'; column_mode: 1 | 2 }) => void;
  includeSolution: boolean;
  referenceSources: { title: string; url: string }[];
  matrix: ExamMatrix;
  questions: Question[];
  examMeta: {
    school_name: string;
    exam_name: string;
    academic_year: string;
    exam_code: string;
  };
  onGenerateAll: () => Promise<void>;
  isGeneratingAll: boolean;
  onRegenerateSlot: (slotId: string, customPrompt?: string) => Promise<void>;
  onCloneNumbers: (slotId: string) => Promise<void>;
  onUpdateQuestion: (updatedQ: Question) => void;
  onOpenExport: () => void;
  latexCode: string;
}

export const ExamStudio: React.FC<ExamStudioProps> = ({
  onLayoutChange,
  includeSolution,
  matrix,
  questions,
  referenceSources,
  examMeta,
  onGenerateAll,
  isGeneratingAll,
  onRegenerateSlot,
  onCloneNumbers,
  onUpdateQuestion,
  onOpenExport,
  latexCode,
}) => {
  const [activeQuestionIndex, setActiveQuestionIndex] = useState<number>(0);
  const [activePartFilter, setActivePartFilter] = useState<'all' | 'mc' | 'tf' | 'sa' | 'essay'>('all');
  const [rightTab, setRightTab] = useState<'preview' | 'latex'>('preview');
  const [copiedTex, setCopiedTex] = useState<boolean>(false);

  // Cấu hình định dạng trang in A4 và tự động căn chỉnh
  const [columnMode, setColumnMode] = useState<1 | 2>(1);
  const [choiceLayout, setChoiceLayout] = useState<'auto' | '4col' | '2col' | '1col'>('auto');
  const [density, setDensity] = useState<'compact' | 'normal' | 'spacious'>('normal');
  const [fontSize, setFontSize] = useState<'sm' | 'base' | 'lg'>('sm');
  useEffect(() => {
    onLayoutChange({ choice_layout: choiceLayout, density, font_size: fontSize, column_mode: columnMode });
  }, [choiceLayout, density, fontSize, columnMode, onLayoutChange]);
  const [isPreviewExpanded, setIsPreviewExpanded] = useState<boolean>(false);
  const [autoFitNotice, setAutoFitNotice] = useState<string | null>(null);

  const levelBadges = LEVEL_BADGES;

  const scrollToQuestion = (index: number) => {
    setActiveQuestionIndex(index);
    const element = document.getElementById(`question-card-${index}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleCopyLatex = () => {
    navigator.clipboard.writeText(latexCode);
    setCopiedTex(true);
    setTimeout(() => setCopiedTex(false), 2000);
  };

  const filteredQuestions = questions.filter(q => {
    if (activePartFilter === 'all') return true;
    if (activePartFilter === 'mc') return q.type === "MULTIPLE_CHOICE";
    if (activePartFilter === 'tf') return q.type === "TRUE_FALSE";
    if (activePartFilter === 'sa') return q.type === "SHORT_ANSWER";
    if (activePartFilter === 'essay') return q.type === "ESSAY";
    return true;
  });

  // Tự động đo độ dài phương án để xếp 4 cột, 2 cột hay 1 cột
  const getChoiceGridClass = (choices?: string[], layoutSetting: 'auto' | '4col' | '2col' | '1col' = 'auto') => {
    if (!choices || choices.length === 0) return 'grid-cols-2';
    if (layoutSetting === '4col') return 'grid-cols-4';
    if (layoutSetting === '2col') return 'grid-cols-2';
    if (layoutSetting === '1col') return 'grid-cols-1';

    // Chế độ tự động thông minh:
    const maxLen = Math.max(...choices.map(c => (c || '').trim().length));
    if (maxLen <= 18) return 'grid-cols-4'; // Rất ngắn (số, biến đơn) -> 1 hàng 4 cột
    if (maxLen <= 42) return 'grid-cols-2'; // Trung bình -> 2 hàng 2 cột
    return 'grid-cols-1';                   // Dài -> 4 hàng 1 cột
  };

  // Tính năng "Tự sắp xếp cho vừa A4"
  const handleAutoFitA4 = () => {
    const total = questions.length;
    setChoiceLayout('auto');

    if (total <= 8) {
      // Đề ngắn: 1 cột, chuẩn
      setColumnMode(1);
      setDensity('normal');
      setFontSize('base');
    } else {
      setColumnMode(2);
      setDensity('compact');
      setFontSize('sm');
    }

    setAutoFitNotice("Đã điều chỉnh bố cục A4.");
    setTimeout(() => setAutoFitNotice(null), 4500);
  };

  // Đính kèm metadata phân loại Phần cho từng câu hỏi
  const annotatedQuestions = useMemo(() => {
    let currentType: string | null = null;
    let partCounter = 0;
    const romanMap = ['I', 'II', 'III', 'IV', 'V', 'VI'];

    return questions.map((q, idx) => {
      let isFirstOfPart = false;
      let partTitle = '';
      let partDesc = '';

      if (q.type !== currentType) {
        currentType = q.type;
        isFirstOfPart = true;
        const roman = romanMap[partCounter] || `${partCounter + 1}`;
        partCounter++;

        if (q.type === 'MULTIPLE_CHOICE') {
          partTitle = `PHẦN ${roman}. Câu trắc nghiệm nhiều phương án lựa chọn.`;
          partDesc = 'Thí sinh trả lời từng câu hỏi. Mỗi câu hỏi thí sinh chỉ chọn một phương án.';
        } else if (q.type === 'TRUE_FALSE') {
          partTitle = `PHẦN ${roman}. Câu trắc nghiệm đúng sai.`;
          partDesc = 'Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.';
        } else if (q.type === 'SHORT_ANSWER') {
          partTitle = `PHẦN ${roman}. Câu trắc nghiệm trả lời ngắn.`;
          partDesc = 'Thí sinh điền kết quả vào ô tương ứng.';
        } else if (q.type === 'ESSAY') {
          partTitle = `PHẦN ${roman}. Tự luận.`;
          partDesc = 'Thí sinh trình bày chi tiết các bước giải và lập luận trên giấy làm bài.';
        }
      }

      return {
        ...q,
        globalIndex: idx + 1,
        isFirstOfPart,
        partTitle,
        partDesc
      };
    });
  }, [questions]);

  const previewRef = useRef<HTMLDivElement>(null);
  const [measurements, setMeasurements] = useState({
    heights: [] as number[], firstCapacity: 0, nextCapacity: 0,
  });
  const pageHeight = isPreviewExpanded ? 1070 : 720;

  const paginatedPages = useMemo(() => {
    const pages: { pageIndex: number; items: typeof annotatedQuestions }[] = [];
    let items: typeof annotatedQuestions = [];
    let height = 0;
    let column = 1;

    for (const question of annotatedQuestions) {
      const questionHeight = measurements.heights[question.globalIndex - 1];
      const capacity = pages.length === 0 ? measurements.firstCapacity : measurements.nextCapacity;
      if (items.length && questionHeight && capacity && height + questionHeight > capacity) {
        if (column === columnMode) {
          pages.push({ pageIndex: pages.length + 1, items });
          items = [];
          column = 1;
        } else {
          column++;
        }
        height = 0;
      }
      items.push(question);
      height += questionHeight || 0;
    }
    if (items.length) pages.push({ pageIndex: pages.length + 1, items });
    return pages;
  }, [annotatedQuestions, columnMode, measurements]);

  useLayoutEffect(() => {
    const preview = previewRef.current;
    if (!preview) return;

    const sheets = Array.from(preview.querySelectorAll<HTMLElement>('.a4-sheet'));
    const questions = Array.from(preview.querySelectorAll<HTMLElement>('[data-print-question]'));
    const measure = () => {
      const heights: number[] = [];
      for (const question of questions) {
        const style = getComputedStyle(question);
        heights[Number(question.dataset.printQuestion) - 1] = Math.ceil(
          question.offsetHeight + parseFloat(style.marginTop) + parseFloat(style.marginBottom)
        );
      }
      const first = sheets[0];
      if (!first) return;
      const style = getComputedStyle(first);
      const verticalInsets = ['paddingTop', 'paddingBottom', 'borderTopWidth', 'borderBottomWidth']
        .reduce((sum, property) => sum + parseFloat(style[property as keyof CSSStyleDeclaration] as string), 0);
      const outerHeight = (element: HTMLElement | null) =>
        element ? element.offsetHeight + parseFloat(getComputedStyle(element).marginTop)
          + parseFloat(getComputedStyle(element).marginBottom) : 0;
      const firstHeader = outerHeight(first.querySelector('[data-print-header]'));
      const nextHeader = sheets[1]
        ? outerHeight(sheets[1].querySelector('[data-print-header]')) : firstHeader;
      const footer = Math.max(...sheets.map(sheet => outerHeight(sheet.querySelector('[data-print-footer]'))));
      const available = pageHeight - verticalInsets - footer;
      const firstCapacity = Math.floor(available - firstHeader);
      const nextCapacity = Math.floor(available - nextHeader);
      setMeasurements(previous =>
        previous.firstCapacity === firstCapacity && previous.nextCapacity === nextCapacity &&
        previous.heights.length === heights.length &&
        heights.every((height, i) => height === previous.heights[i])
          ? previous : { heights, firstCapacity, nextCapacity }
      );
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(preview);
    questions.forEach(question => observer.observe(question));
    sheets.forEach(sheet => {
      sheet.querySelectorAll('[data-print-header], [data-print-footer]').forEach(element => observer.observe(element));
    });
    return () => observer.disconnect();
  }, [paginatedPages, pageHeight, rightTab, density, choiceLayout, fontSize, examMeta, matrix]);

  return (
    <div className="flex flex-col h-[calc(100vh-4.5rem)] overflow-hidden exam-studio-container">
      {/* Top Studio Control Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-2.5 flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-xs no-print">
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 bg-blue-100 text-blue-800 text-xs font-bold rounded-md">
            Lớp {matrix.grade}
          </span>
          <h2 className="text-sm md:text-base font-bold text-slate-900 truncate max-w-md">
            {matrix.title}
          </h2>
          <span className="text-xs text-slate-500 hidden sm:inline">
            • Mã đề: <strong className="text-slate-800">{examMeta.exam_code}</strong> ({matrix.time_minutes} phút)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {referenceSources.length > 0 && (
            <details className="relative text-xs">
              <summary className="cursor-pointer rounded border border-slate-200 px-2 py-1.5">Nguồn tham khảo</summary>
              <ul className="absolute right-0 z-20 mt-1 w-72 space-y-2 rounded border border-slate-200 bg-white p-3 shadow">
                {referenceSources.filter(source => /^https?:\/\//i.test(source.url)).map(source => (
                  <li key={source.url}>
                    <a href={source.url} target="_blank" rel="noopener noreferrer"
                      className="text-blue-700 underline">{source.title}</a>
                  </li>
                ))}
              </ul>
            </details>
          )}
          {/* Nút Sinh toàn bộ đề */}
          <button
            onClick={onGenerateAll}
            disabled={isGeneratingAll}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition-colors duration-150 disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 text-amber-300 ${isGeneratingAll ? 'animate-spin' : ''}`} />
            <span>{isGeneratingAll ? 'Đang sinh đề…' : 'AI Sinh toàn bộ đề'}</span>
          </button>

          {/* Nút Xuất bản & Trộn đề */}
          <button
            onClick={onOpenExport}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 text-xs font-semibold rounded-lg shadow-2xs transition-colors duration-150"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-600" />
            <span>Xuất bản & Trộn đề</span>
          </button>
        </div>
      </div>

      {/* Progress Bar khi đang sinh */}
      {isGeneratingAll && (
        <div className="w-full bg-slate-200 h-1 shrink-0 overflow-hidden no-print">
          <div className="h-full w-1/3 bg-indigo-600 animate-pulse" />
        </div>
      )}

      {/* 3-PANE SPLIT LAYOUT */}
      <div className="flex-1 flex overflow-hidden">
        {/* ========================================================= */}
        {/* CỘT TRÁI: Question Navigator                              */}
        {/* ========================================================= */}
        <aside className={`w-48 lg:w-56 bg-slate-50 border-r border-slate-200 flex flex-col shrink-0 overflow-hidden no-print ${isPreviewExpanded ? 'hidden' : 'flex'}`}>
          <div className="p-3 border-b border-slate-200 bg-white">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
              Điều hướng câu hỏi
            </span>
            <span className="text-[11px] text-slate-500">
              Tổng cộng: {questions.length} / {matrix.slots.length} câu
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {isGeneratingAll ? (
              matrix.slots.map((slot, idx) => {
                const isDone = idx < questions.length;
                const isCurrent = idx === questions.length;
                return (
                  <div
                    key={slot.slot_id || idx}
                    className={`w-full flex items-center justify-between p-2 rounded-lg text-xs font-medium border transition-colors ${
                      isCurrent
                        ? "bg-blue-50/90 border-blue-200 text-blue-900 font-bold"
                        : isDone
                        ? "bg-white border-slate-200 text-slate-800"
                        : "bg-slate-50/50 border-slate-100 text-slate-400 opacity-60"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 truncate">
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 stroke-[1.75] text-emerald-500 shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 className="w-3.5 h-3.5 stroke-[1.75] text-blue-600 animate-spin shrink-0" />
                      ) : (
                        <CircleDashed className="w-3.5 h-3.5 stroke-[1.75] text-slate-300 shrink-0" />
                      )}
                      <span className="w-5 text-left font-mono tabular-nums">
                        {idx + 1}.
                      </span>
                      <span className="truncate">
                        {slot.type === "MULTIPLE_CHOICE" ? "Trắc nghiệm" : slot.type === "TRUE_FALSE" ? "Đúng/Sai" : slot.type === "SHORT_ANSWER" ? "Điền số" : "Tự luận"}
                      </span>
                    </div>

                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                      levelBadges[slot.level]?.color || "bg-slate-100"
                    }`}>
                      {levelBadges[slot.level]?.label}
                    </span>
                  </div>
                );
              })
            ) : (
              questions.map((q, idx) => {
                const isSelected = activeQuestionIndex === idx;
                return (
                  <button
                    key={q.id || idx}
                    onClick={() => scrollToQuestion(idx)}
                    className={`w-full flex items-center justify-between p-2 rounded-lg text-xs font-medium transition-colors duration-150 ${
                      isSelected 
                        ? "bg-blue-600 text-white shadow-xs font-bold" 
                        : "bg-white hover:bg-slate-100 text-slate-700 border border-slate-100"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="w-5 text-left font-mono">
                        {idx + 1}.
                      </span>
                      <span className="truncate">
                        {q.type === "MULTIPLE_CHOICE" ? "Trắc nghiệm" : q.type === "TRUE_FALSE" ? "Đúng/Sai" : q.type === "SHORT_ANSWER" ? "Điền số" : "Tự luận"}
                      </span>
                    </div>

                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                      isSelected ? "bg-white/20 text-white" : levelBadges[q.level]?.color || "bg-slate-100"
                    }`}>
                      {levelBadges[q.level]?.label}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </aside>

        {/* ========================================================= */}
        {/* CỘT GIỮA: Interactive Question Cards                      */}
        {/* ========================================================= */}
        <section className={`flex-1 min-w-[340px] flex flex-col bg-slate-100 overflow-hidden border-r border-slate-200 no-print ${isPreviewExpanded ? 'hidden' : 'flex'}`}>
          {/* Filter Bar */}
          <div className="bg-white border-b border-slate-200 px-4 py-2 flex items-center justify-between gap-2 shrink-0">
            <div className="flex items-center gap-1 overflow-x-auto">
              {[
                { id: 'all', label: `Tất cả (${questions.length})` },
                ...(questions.some(q => q.type === "MULTIPLE_CHOICE") ? [{ id: 'mc', label: `Trắc nghiệm (${questions.filter(q => q.type === "MULTIPLE_CHOICE").length})` }] : []),
                ...(questions.some(q => q.type === "TRUE_FALSE") ? [{ id: 'tf', label: `Đúng/Sai (${questions.filter(q => q.type === "TRUE_FALSE").length})` }] : []),
                ...(questions.some(q => q.type === "SHORT_ANSWER") ? [{ id: 'sa', label: `Trả lời ngắn (${questions.filter(q => q.type === "SHORT_ANSWER").length})` }] : []),
                ...(questions.some(q => q.type === "ESSAY") ? [{ id: 'essay', label: `Tự luận (${questions.filter(q => q.type === "ESSAY").length})` }] : []),
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActivePartFilter(tab.id as any)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold whitespace-nowrap transition-colors duration-150 ${
                    activePartFilter === tab.id
                      ? "bg-slate-800 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <span className="text-[11px] text-slate-400 font-medium hidden md:inline">
              KaTeX Live Preview
            </span>
          </div>

          {/* Question Cards List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isGeneratingAll && (
              /* A. AI Progress Command Card (Thẻ Tiến trình Trung tâm) */
              <div className="bg-white border border-blue-200/90 shadow-lg shadow-blue-500/5 rounded-2xl p-5 mb-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0">
                      <Loader2 className="w-6 h-6 stroke-[1.75] animate-spin" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900 tracking-tight">
                        AI đang biên soạn đề thi theo ma trận đặc tả...
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                        Đang xử lý: <strong className="text-blue-700">
                          {matrix.slots[Math.min(questions.length, matrix.slots.length - 1)]?.part === 1 ? 'Phần I - Trắc nghiệm 4 lựa chọn' : matrix.slots[Math.min(questions.length, matrix.slots.length - 1)]?.part === 2 ? 'Phần II - Trắc nghiệm Đúng/Sai' : 'Phần III - Trả lời ngắn'}
                        </strong> • {matrix.slots[Math.min(questions.length, matrix.slots.length - 1)]?.topic}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="tabular-nums text-2xl font-bold text-blue-600 leading-none">
                      {String(questions.length).padStart(2, '0')} / {String(matrix.slots.length).padStart(2, '0')}
                    </div>
                    <div className="text-xs font-semibold text-slate-500 mt-1 tabular-nums">
                      ({matrix.slots.length > 0 ? Math.round((questions.length / matrix.slots.length) * 100) : 0}%)
                    </div>
                  </div>
                </div>

                {/* Thanh Progress Bar Đa tầng (Solid Color) */}
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden my-4 p-0.5">
                  <div 
                    className="h-full bg-blue-600 transition-all duration-500 ease-out rounded-full"
                    style={{ width: `${Math.max(matrix.slots.length > 0 ? Math.round((questions.length / matrix.slots.length) * 100) : 0, 8)}%` }}
                  />
                </div>

                {/* 4 Bước Pipeline Trực quan (4-Step Pipeline Checklist) */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 stroke-[1.75] text-emerald-600 shrink-0" />
                    <span className="text-slate-700 font-medium">Phân tích ma trận ({matrix.slots.length} slots)</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {questions.length >= matrix.slots.length ? (
                      <CheckCircle2 className="w-4 h-4 stroke-[1.75] text-emerald-600 shrink-0" />
                    ) : (
                      <Loader2 className="w-4 h-4 stroke-[1.75] text-blue-600 animate-spin shrink-0" />
                    )}
                    <span className={questions.length >= matrix.slots.length ? "text-slate-700 font-medium" : "text-blue-700 font-semibold"}>
                      Sinh câu hỏi & Công thức LaTeX
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {questions.length >= matrix.slots.length ? (
                      <CheckCircle2 className="w-4 h-4 stroke-[1.75] text-emerald-600 shrink-0" />
                    ) : questions.length > Math.floor(matrix.slots.length / 2) ? (
                      <Loader2 className="w-4 h-4 stroke-[1.75] text-indigo-600 animate-spin shrink-0" />
                    ) : (
                      <CircleDashed className="w-4 h-4 stroke-[1.75] text-slate-300 shrink-0" />
                    )}
                    <span className="text-slate-600 font-medium">Kiểm chứng đáp án & Lời giải</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {questions.length >= matrix.slots.length ? (
                      <CheckCircle2 className="w-4 h-4 stroke-[1.75] text-emerald-600 shrink-0" />
                    ) : (
                      <CircleDashed className="w-4 h-4 stroke-[1.75] text-slate-300 shrink-0" />
                    )}
                    <span className="text-slate-600 font-medium">Đóng gói chuẩn ex_test.sty</span>
                  </div>
                </div>
              </div>
            )}

            {/* Thẻ câu hỏi thật đã hoàn thành */}
            {filteredQuestions.map((q, idx) => (
              <QuestionCard
                key={q.id || idx}
                question={q}
                index={idx}
                isActive={activeQuestionIndex === idx}
                onRegenerate={(prompt) => onRegenerateSlot(q.id, prompt)}
                onCloneNumbers={() => onCloneNumbers(q.id)}
                onUpdate={onUpdateQuestion}
              />
            ))}

            {/* B. Live Streaming: 3 Question Skeleton Cards mô phỏng cấu trúc câu hỏi */}
            {isGeneratingAll && Array.from({ length: Math.min(3, Math.max(1, matrix.slots.length - questions.length)) }).map((_, k) => {
              const targetSlot = matrix.slots[questions.length + k];
              if (!targetSlot) return null;
              return (
                <div key={`skeleton-${k}`} className="bg-white border border-slate-200/80 rounded-xl p-5 space-y-4 shadow-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-800 tabular-nums">
                        Câu {targetSlot.slot_number}.
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200/70">
                        {levelBadges[targetSlot.level]?.label} • {targetSlot.topic}
                      </span>
                    </div>
                    <span className="inline-flex items-center gap-1.5 text-xs text-blue-600 font-semibold bg-blue-50/70 px-2.5 py-1 rounded-md border border-blue-100">
                      <Loader2 className="w-3.5 h-3.5 stroke-[1.75] animate-spin" />
                      <span>Đang biên soạn...</span>
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="h-4 bg-slate-200/70 rounded w-3/4 animate-pulse" />
                    <div className="h-4 bg-slate-200/70 rounded w-1/2 animate-pulse" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {["A", "B", "C", "D"].map((letter) => (
                      <div key={letter} className="h-10 bg-slate-50 border border-slate-100 rounded-lg p-2.5 flex items-center gap-2 animate-pulse">
                        <span className="w-5 h-5 rounded-full bg-slate-200/80 text-slate-500 font-bold text-[10px] flex items-center justify-center">
                          {letter}
                        </span>
                        <div className="h-2.5 bg-slate-200/70 rounded w-2/3" />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            {!isGeneratingAll && filteredQuestions.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                <Sparkles className="w-10 h-10 stroke-[1.75] text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-slate-600">Chưa có câu hỏi nào</p>
                <p className="text-xs text-slate-400 mt-1">Bấm "AI Sinh toàn bộ đề" ở thanh trên để bắt đầu.</p>
              </div>
            )}
          </div>
        </section>

        {/* ========================================================= */}
        {/* CỘT PHẢI: Live Preview (KaTeX A4 / .tex / PDF)            */}
        {/* ========================================================= */}
        <aside className={`${isPreviewExpanded ? "flex-1 w-full" : "w-[430px] xl:w-[520px]"} bg-white flex flex-col shrink-0 overflow-hidden a4-print-scope transition-[width] duration-200`}>
          {/* Tabs header */}
          <div className="bg-slate-100 border-b border-slate-200 px-3 py-2 flex items-center justify-between shrink-0 no-print">
            <div className="flex items-center gap-1 bg-slate-200/80 p-0.5 rounded-lg text-xs font-semibold">
              <button
                onClick={() => startTransition(() => setRightTab('preview'))}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  rightTab === 'preview' 
                    ? "bg-white text-blue-700 shadow-xs font-bold" 
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Bản in Web (A4)</span>
              </button>

              <button
                onClick={() => startTransition(() => setRightTab('latex'))}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  rightTab === 'latex' 
                    ? "bg-white text-blue-700 shadow-xs font-bold" 
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Code className="w-3.5 h-3.5" />
                <span>Mã nguồn .tex</span>
              </button>

            </div>

            {/* Quick Actions at Top Right */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsPreviewExpanded(!isPreviewExpanded)}
                className="p-1 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-200"
                title={isPreviewExpanded ? "Thu gọn bản xem" : "Mở rộng toàn màn hình"}
              >
                {isPreviewExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Tab 1: Web Paper Preview (A4 Chuẩn & Tự căn chỉnh) */}
          {rightTab === 'preview' && (
            <ViewTransition enter="fade-in" exit="fade-out">
              <div className="flex-1 flex flex-col overflow-hidden bg-slate-200/70 a4-preview-pane">
              {/* SUB-TOOLBAR CHO BẢN IN A4 */}
              <div className="bg-white border-b border-slate-200 px-3 py-2 flex flex-wrap items-center justify-between gap-2 shrink-0 text-xs no-print shadow-2xs">
                {/* Nút Magic: Tự động sắp xếp vừa A4 */}
                <button
                  onClick={handleAutoFitA4}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 font-semibold rounded-lg shadow-2xs transition-colors duration-150 cursor-pointer"
                  title="Tự động tính toán số câu, phương án và phân bổ vừa khít số trang A4 chuẩn"
                >
                  <Wand2 className="w-3.5 h-3.5 text-blue-600" />
                  <span>Tự sắp xếp vừa A4</span>
                </button>

                <div className="flex items-center gap-1.5 flex-wrap">
                  {/* Bố cục cột: 1 cột / 2 cột */}
                  <div className="flex items-center bg-slate-100 border border-slate-300 rounded-md p-0.5">
                    <button
                      onClick={() => setColumnMode(1)}
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${columnMode === 1 ? "bg-white text-blue-700 shadow-2xs" : "text-slate-600 hover:text-slate-900"}`}
                      title="1 Cột chuẩn"
                    >
                      1 Cột
                    </button>
                    <button
                      onClick={() => setColumnMode(2)}
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${columnMode === 2 ? "bg-blue-600 text-white shadow-2xs" : "text-slate-600 hover:text-slate-900"}`}
                      title="2 Cột (Chuẩn đề thi THPT Bộ GD&ĐT - Tiết kiệm giấy)"
                    >
                      2 Cột (Bộ GD)
                    </button>
                  </div>

                  {/* Bố trí đáp án A-B-C-D */}
                  <select
                    value={choiceLayout}
                    onChange={(e) => setChoiceLayout(e.target.value as any)}
                    className="bg-white border border-slate-300 rounded-md px-2 py-1 text-[11px] font-medium text-slate-700 focus:outline-none"
                    title="Cách xếp phương án A, B, C, D"
                  >
                    <option value="auto">Đáp án: Tự động</option>
                    <option value="4col">Đáp án: 4 Cột (1 dòng)</option>
                    <option value="2col">Đáp án: 2 Cột (2 dòng)</option>
                    <option value="1col">Đáp án: 1 Cột (4 dòng)</option>
                  </select>

                  {/* Giãn cách */}
                  <select
                    value={density}
                    onChange={(e) => setDensity(e.target.value as any)}
                    className="bg-white border border-slate-300 rounded-md px-2 py-1 text-[11px] font-medium text-slate-700 focus:outline-none"
                    title="Mật độ dòng và khoảng cách câu"
                  >
                    <option value="compact">Giãn cách: Chặt chẽ</option>
                    <option value="normal">Giãn cách: Tiêu chuẩn</option>
                    <option value="spacious">Giãn cách: Thoáng</option>
                  </select>

                  {/* Cỡ chữ */}
                  <select
                    value={fontSize}
                    onChange={(e) => setFontSize(e.target.value as any)}
                    className="bg-white border border-slate-300 rounded-md px-2 py-1 text-[11px] font-medium text-slate-700 focus:outline-none"
                    title="Cỡ chữ đề thi"
                  >
                    <option value="sm">Chữ: 11pt (Chuẩn)</option>
                    <option value="base">Chữ: 12pt</option>
                    <option value="lg">Chữ: 13pt (Lớn)</option>
                  </select>

                  {/* Nút In A4 trực tiếp */}
                  <button
                    onClick={() => window.print()}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-md shadow-xs transition"
                    title="In trực tiếp ra máy in hoặc lưu PDF A4"
                  >
                    <Printer className="w-3.5 h-3.5 text-emerald-400" />
                    <span>In A4</span>
                  </button>
                </div>
              </div>

              {/* Thông báo Tự sắp xếp thành công */}
              {autoFitNotice && (
                <div className="bg-amber-50 border-b border-amber-200 text-amber-900 px-4 py-1.5 text-xs font-semibold flex items-center justify-between no-print animate-in fade-in">
                  <span>{autoFitNotice}</span>
                  <button onClick={() => setAutoFitNotice(null)} className="text-amber-600 hover:text-amber-900 font-bold ml-2">×</button>
                </div>
              )}

              {/* KHU VỰC CUỘN CÁC TRANG GIẤY A4 MÔ PHỎNG */}
              <div ref={previewRef} className="a4-preview-pages flex-1 overflow-y-auto p-4 flex flex-col items-center gap-6">
                {paginatedPages.length === 0 ? (
                  isGeneratingAll ? (
                    /* Paper Skeleton khi đang AI sinh đề */
                    <div 
                      className={`a4-sheet w-full ${isPreviewExpanded ? "max-w-[760px] p-8" : "max-w-[480px] xl:max-w-[540px] p-6"} text-slate-900 exam-paper-font flex flex-col justify-between relative bg-white border border-slate-200 rounded-lg shadow-sm`}
                      style={{ minHeight: pageHeight }}
                    >
                      {/* Floating Pill ở giữa trang giấy */}
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900/90 text-white rounded-full shadow-xl backdrop-blur-md text-xs font-semibold">
                          <Loader2 className="w-4 h-4 stroke-[1.75] text-blue-400 animate-spin" />
                          <span>Đang dàn trang LaTeX A4 ({questions.length}/{matrix.slots.length} câu)...</span>
                        </div>
                      </div>

                      <div>
                        {/* Header đề thi chuẩn Bộ GD&ĐT */}
                        <div className="border-b border-slate-900 pb-3 mb-4">
                          <div className="flex justify-between items-start gap-2">
                            <div className="text-center font-bold text-[11px] leading-tight flex-1">
                              <div>{examMeta.school_name}</div>
                              <div>{examMeta.exam_name}</div>
                              <div className="font-normal italic text-[10px]">Năm học: {examMeta.academic_year}</div>
                            </div>
                            <div className="text-center text-[11px] leading-tight flex-1">
                              <div className="font-bold">{matrix.title}</div>
                              <div className="text-[10px] mt-0.5">Thời gian làm bài: {matrix.time_minutes} phút</div>
                              <div className="font-bold text-[10px]">Mã đề thi: {examMeta.exam_code}</div>
                            </div>
                          </div>
                          <div className="text-center italic text-[9px] mt-1 text-slate-500">
                            (Đề thi có {Math.max(1, Math.ceil(matrix.slots.length / 10))} trang)
                          </div>
                        </div>

                        {/* Skeleton các dòng câu hỏi trên giấy A4 */}
                        <div className="space-y-4 opacity-70">
                          <div className="h-3.5 bg-slate-200/80 rounded w-2/5 animate-pulse" />
                          <div className="space-y-2 pl-3">
                            <div className="h-3 bg-slate-200/60 rounded w-11/12 animate-pulse" />
                            <div className="h-3 bg-slate-200/60 rounded w-4/5 animate-pulse" />
                            <div className="grid grid-cols-2 gap-2 pt-1">
                              <div className="h-2.5 bg-slate-100 rounded w-3/4 animate-pulse" />
                              <div className="h-2.5 bg-slate-100 rounded w-3/4 animate-pulse" />
                              <div className="h-2.5 bg-slate-100 rounded w-3/4 animate-pulse" />
                              <div className="h-2.5 bg-slate-100 rounded w-3/4 animate-pulse" />
                            </div>
                          </div>

                          <div className="h-3.5 bg-slate-200/80 rounded w-1/3 animate-pulse pt-2" />
                          <div className="space-y-2 pl-3">
                            <div className="h-3 bg-slate-200/60 rounded w-full animate-pulse" />
                            <div className="h-3 bg-slate-200/60 rounded w-2/3 animate-pulse" />
                            <div className="grid grid-cols-2 gap-2 pt-1">
                              <div className="h-2.5 bg-slate-100 rounded w-3/4 animate-pulse" />
                              <div className="h-2.5 bg-slate-100 rounded w-3/4 animate-pulse" />
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="text-center text-[10px] text-slate-400 border-t border-slate-200 pt-2 font-mono">
                        Trang 1 / {Math.max(1, Math.ceil(matrix.slots.length / 10))}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white p-8 rounded-lg shadow-sm text-center text-slate-400 text-xs">
                      Chưa có câu hỏi nào để hiển thị.
                    </div>
                  )
                ) : (
                  paginatedPages.map((page) => {
                    const isFirstPage = page.pageIndex === 1;
                    const isLastPage = page.pageIndex === paginatedPages.length;

                    return (
                      <div
                        key={page.pageIndex}
                        className={`a4-sheet w-full ${isPreviewExpanded ? "max-w-[760px] p-8" : "max-w-[480px] xl:max-w-[540px] p-6"} text-slate-900 exam-paper-font flex flex-col justify-between`}
                        style={{ minHeight: pageHeight }}
                      >
                        <div>
                          {/* HEADER TRANG 1 (Chuẩn Bộ Giáo Dục & Đào Tạo) */}
                          {isFirstPage ? (
                            <div data-print-header className="border-b border-slate-900 pb-3 mb-4">
                              <div className="flex justify-between items-start gap-2">
                                <div className="text-center font-bold text-[11px] leading-tight flex-1">
                                  <div>{examMeta.school_name}</div>
                                  <div>{examMeta.exam_name}</div>
                                  <div className="font-normal italic text-[10px]">Năm học: {examMeta.academic_year}</div>
                                </div>
                                <div className="text-center text-[11px] leading-tight flex-1">
                                  <div className="font-bold">{matrix.title}</div>
                                  <div className="italic text-[10px]">Thời gian làm bài: {matrix.time_minutes} phút</div>
                                  <div className="font-bold mt-0.5">Mã đề thi: {examMeta.exam_code}</div>
                                </div>
                              </div>
                              <div className="text-center italic text-[10px] text-slate-500 mt-1">
                                (Đề thi có {paginatedPages.length} trang)
                              </div>
                            </div>
                          ) : (
                            /* HEADER CÁC TRANG TIẾP THEO (Rút gọn) */
                            <div data-print-header className="flex justify-between items-center text-[10px] text-slate-500 border-b border-slate-300 pb-1.5 mb-4">
                              <span className="font-medium uppercase tracking-wide">
                                {matrix.title} • Mã đề: {examMeta.exam_code}
                              </span>
                              <span className="italic">
                                Trang {page.pageIndex}/{paginatedPages.length}
                              </span>
                            </div>
                          )}

                          {/* DANH SÁCH CÂU HỎI TRONG TRANG */}
                          <div className={columnMode === 2 ? "two-column-exam" : undefined}>
                            {page.items.map((q) => {
                              const choiceGrid = getChoiceGridClass(q.choices, choiceLayout);

                              return (
                                <div key={q.id || q.globalIndex} data-print-question={q.globalIndex} className={`question-avoid-break flow-root ${density === "compact" ? "pb-2.5" : density === "spacious" ? "pb-4" : "pb-3"}`}>
                                  {/* Tiêu đề phân đoạn Phần I, Phần II, Phần III */}
                                  {q.isFirstOfPart && (
                                    <div className="mb-2 pb-1 border-b border-slate-300">
                                      <div className="font-bold text-[11px] text-slate-900 leading-tight">
                                        {q.partTitle}
                                      </div>
                                      {q.partDesc && (
                                        <div className="italic text-[10px] text-slate-600 leading-tight">
                                          {q.partDesc}
                                        </div>
                                      )}
                                    </div>
                                  )}

                                  {/* Nội dung câu hỏi */}
                                  <div className="space-y-1">
                                    <div className={`font-bold flex items-start gap-1 ${fontSize === 'lg' ? 'text-xs' : 'text-[11px]'}`}>
                                      <span className="shrink-0 font-bold">Câu {q.globalIndex}.</span>
                                      <div className="font-normal flex-1 leading-relaxed">
                                        <MathView text={q.stem} />
                                      </div>
                                    </div>

                                    {/* Hình vẽ TikZ / Bảng biến thiên trực quan khi in A4 */}
                                    {q.tikz_code && q.tikz_code.trim() && (
                                      <TikZView tikzCode={q.tikz_code} printMode={true} />
                                    )}

                                    {/* Phương án trắc nghiệm 4 lựa chọn (Phần I) */}
                                    {q.type === "MULTIPLE_CHOICE" && q.choices && (
                                      <div className={`grid ${choiceGrid} gap-x-2 gap-y-1 pl-3 pt-0.5 font-sans text-[11px]`}>
                                        {q.choices.map((c, i) => (
                                          <div key={i} className="flex items-start gap-1">
                                            <span className="font-bold shrink-0">{["A", "B", "C", "D"][i]}.</span>
                                            <div className="min-w-0 flex-1 overflow-visible">
                                              <MathView text={c} />
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Đúng / Sai (Phần II) */}
                                    {q.type === "TRUE_FALSE" && q.statements && (
                                      <div className="space-y-0.5 pl-3 pt-0.5 font-sans text-[11px]">
                                        {q.statements.map((s, i) => (
                                          <div key={i} className="flex items-start gap-1">
                                            <span className="font-bold shrink-0">{["a)", "b)", "c)", "d)"][i]}</span>
                                            <div className="flex-1">
                                              <MathView text={s.statement} />
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Trả lời ngắn (Phần III) */}
                                    {q.type === "SHORT_ANSWER" && (
                                      <div className="pl-3 pt-0.5 font-sans text-[11px]">
                                        <span className="italic text-slate-500 font-medium">Đáp số: [..........]</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        {/* FOOTER TRANG IN CHUẨN */}
                        <div data-print-footer className="border-t border-slate-300 pt-2 mt-4 text-center text-[10px] text-slate-500">
                          {isLastPage ? (
                            <div>
                              <div className="font-bold text-slate-700 tracking-wider">---------- HẾT ----------</div>
                              <div className="italic mt-0.5">Trang {page.pageIndex} / {paginatedPages.length}</div>
                            </div>
                          ) : (
                            <div className="flex justify-between items-center text-[10px]">
                              <span className="italic">Thí sinh không được sử dụng tài liệu</span>
                              <span className="font-medium">Trang {page.pageIndex} / {paginatedPages.length}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </ViewTransition>
        )}

          {/* Tab 2: Full LaTeX Source (.tex) */}
          {rightTab === 'latex' && (
            <ViewTransition enter="fade-in" exit="fade-out">
              <div className="flex-1 flex flex-col bg-slate-950 p-3 overflow-hidden">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs text-slate-400">
                  <span className="font-mono text-slate-300">ex_test.sty format (Chuẩn 2026)</span>
                  <button
                    onClick={handleCopyLatex}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-semibold text-xs focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {copiedTex ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedTex ? 'Đã sao chép' : 'Sao chép .tex'}</span>
                  </button>
                </div>

                <textarea
                  readOnly
                  aria-label="Mã nguồn LaTeX của đề thi"
                  value={latexCode}
                  className="flex-1 w-full bg-slate-900 text-slate-100 font-mono text-[11px] p-3 rounded-lg border border-slate-800 focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 resize-none overflow-y-auto leading-relaxed select-all"
                />
              </div>
            </ViewTransition>
          )}

        </aside>
      </div>
      {questions.length > 0 && (
        <section className="print-paper hidden" aria-label="Đề thi để in">
          <div className="print-paper-heading">
            <div>
              <strong>{examMeta.school_name}</strong>
              <div>{examMeta.exam_name}</div>
              <div>Năm học {examMeta.academic_year}</div>
            </div>
            <div>
              <strong>{matrix.title}</strong>
              <div>Thời gian làm bài {matrix.time_minutes} phút</div>
              <div>Mã đề {examMeta.exam_code}</div>
            </div>
          </div>
          {annotatedQuestions.map(question => (
            <div key={question.id} className="print-paper-question question-avoid-break">
              {question.isFirstOfPart && (
                <div className="print-paper-part">
                  <strong>{question.partTitle}</strong>
                  <div>{question.partDesc}</div>
                </div>
              )}
              <div className="print-paper-stem">
                <strong>Câu {question.globalIndex}. </strong>
                <MathView text={question.stem} />
              </div>
              {question.type === 'MULTIPLE_CHOICE' && question.choices && (
                <div className="print-paper-choices">
                  {question.choices.map((choice, index) => (
                    <div key={index}><strong>{'ABCD'[index]}. </strong><MathView text={choice} /></div>
                  ))}
                </div>
              )}
              {question.type === 'TRUE_FALSE' && question.statements && (
                <div className="print-paper-statements">
                  {question.statements.map((statement, index) => (
                    <div key={index}><strong>{'abcd'[index]}) </strong><MathView text={statement.statement} /></div>
                  ))}
                </div>
              )}
              {question.type === 'SHORT_ANSWER' && <div>Đáp số ................................</div>}
            </div>
          ))}
          <div className="print-paper-end">HẾT</div>
        </section>
      )}
      {includeSolution && questions.length > 0 && (
        <section className="print-solutions hidden">
          <h2>ĐÁP ÁN VÀ LỜI GIẢI</h2>
          {questions.map((question, index) => (
            <div key={question.id} className="question-avoid-break mb-3">
              <strong>Câu {index + 1}. </strong>
              {question.type === 'MULTIPLE_CHOICE' && question.correct_index != null &&
                <span>Đáp án {'ABCD'[question.correct_index]}. </span>}
              {question.type === 'SHORT_ANSWER' && question.correct_value &&
                <span>Đáp số {question.correct_value}. </span>}
              {question.type === 'TRUE_FALSE' && question.statements &&
                <span>{question.statements.map((item, i) =>
                  `${'abcd'[i]}) ${item.is_correct ? 'Đúng' : 'Sai'}`).join('; ')}. </span>}
              <MathView text={question.solution} />
            </div>
          ))}
        </section>
      )}
    </div>
  );
};
