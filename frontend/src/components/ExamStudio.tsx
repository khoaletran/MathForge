import React, { useState, useMemo, startTransition, ViewTransition } from 'react';
import { 
  Sparkles, FileText, CheckCircle2, RefreshCw, Printer, 
  Copy, Check, Code, Eye, FileDown, Layers, ChevronRight, 
  AlertCircle, ShieldCheck, Download, ExternalLink, SlidersHorizontal,
  Columns, Maximize2, Minimize2, Wand2
} from 'lucide-react';
import { QuestionCard, Question } from './QuestionCard';
import { MathView } from './MathView';
import { ExamMatrix } from './MatrixManager';

interface ExamStudioProps {
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
  progress: { current: number; total: number };
  onRegenerateSlot: (slotId: string, customPrompt?: string) => Promise<void>;
  onCloneNumbers: (slotId: string) => Promise<void>;
  onUpdateQuestion: (updatedQ: Question) => void;
  onOpenExport: () => void;
  latexCode: string;
  onCompilePdf: () => Promise<void>;
  isCompiling: boolean;
}

export const ExamStudio: React.FC<ExamStudioProps> = ({
  matrix,
  questions,
  examMeta,
  onGenerateAll,
  isGeneratingAll,
  progress,
  onRegenerateSlot,
  onCloneNumbers,
  onUpdateQuestion,
  onOpenExport,
  latexCode,
  onCompilePdf,
  isCompiling
}) => {
  const [activeQuestionIndex, setActiveQuestionIndex] = useState<number>(0);
  const [activePartFilter, setActivePartFilter] = useState<'all' | 1 | 2 | 3>('all');
  const [rightTab, setRightTab] = useState<'preview' | 'latex' | 'pdf'>('preview');
  const [copiedTex, setCopiedTex] = useState<boolean>(false);

  // Cấu hình định dạng trang in A4 và tự động căn chỉnh
  const [columnMode, setColumnMode] = useState<1 | 2>(1);
  const [choiceLayout, setChoiceLayout] = useState<'auto' | '4col' | '2col' | '1col'>('auto');
  const [density, setDensity] = useState<'compact' | 'normal' | 'spacious'>('normal');
  const [fontSize, setFontSize] = useState<'sm' | 'base' | 'lg'>('sm');
  const [isPreviewExpanded, setIsPreviewExpanded] = useState<boolean>(false);
  const [autoFitNotice, setAutoFitNotice] = useState<string | null>(null);

  const levelBadges = {
    NHAN_BIET: { label: "NB", color: "bg-emerald-100 text-emerald-800" },
    THONG_HIEU: { label: "TH", color: "bg-blue-100 text-blue-800" },
    VAN_DUNG: { label: "VD", color: "bg-amber-100 text-amber-800" },
    VAN_DUNG_CAO: { label: "VDC", color: "bg-rose-100 text-rose-800" }
  };

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
    if (activePartFilter === 1) return q.type === "MULTIPLE_CHOICE";
    if (activePartFilter === 2) return q.type === "TRUE_FALSE";
    if (activePartFilter === 3) return q.type === "SHORT_ANSWER";
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
      setAutoFitNotice(`✨ Đã tự động bố trí ${total} câu vừa khít 1 trang A4!`);
    } else if (total <= 24) {
      // Đề chuẩn tốt nghiệp THPT 2025 (22 câu): xếp vừa khít 2 trang A4 (1 tờ 2 mặt)
      setColumnMode(2);
      setDensity('compact');
      setFontSize('sm');
      setAutoFitNotice(`✨ Đã tự động sắp xếp ${total} câu vừa khít 2 trang A4 (1 tờ 2 mặt) theo chuẩn Bộ GD&ĐT!`);
    } else {
      // Đề thi học kỳ / thi thử lớn (30 - 50 câu): xếp vào 4 trang A4 (2 tờ in)
      setColumnMode(2);
      setDensity('compact');
      setFontSize('sm');
      setAutoFitNotice(`✨ Đã tối ưu ${total} câu vừa vặn vào 4 trang A4 (2 tờ in) tiết kiệm giấy tối đa!`);
    }

    setTimeout(() => setAutoFitNotice(null), 4500);
  };

  // Đính kèm metadata phân loại Phần cho từng câu hỏi
  const annotatedQuestions = useMemo(() => {
    let currentType: string | null = null;
    return questions.map((q, idx) => {
      let isFirstOfPart = false;
      let partTitle = '';
      let partDesc = '';

      if (q.type !== currentType) {
        currentType = q.type;
        isFirstOfPart = true;
        if (q.type === 'MULTIPLE_CHOICE') {
          partTitle = 'PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.';
          partDesc = 'Thí sinh trả lời từng câu hỏi. Mỗi câu hỏi thí sinh chỉ chọn một phương án.';
        } else if (q.type === 'TRUE_FALSE') {
          partTitle = 'PHẦN II. Câu trắc nghiệm đúng sai.';
          partDesc = 'Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.';
        } else if (q.type === 'SHORT_ANSWER') {
          partTitle = 'PHẦN III. Câu trắc nghiệm trả lời ngắn.';
          partDesc = 'Thí sinh điền kết quả vào ô tương ứng.';
        } else if (q.type === 'ESSAY') {
          partTitle = 'PHẦN IV. Tự luận.';
          partDesc = 'Thí sinh trình bày chi tiết các bước giải.';
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

  // Thuật toán chia trang A4 tự động không bao giờ cắt đôi câu hỏi
  const paginatedPages = useMemo(() => {
    if (annotatedQuestions.length === 0) return [];

    // Sức chứa của trang A4 theo điểm tương đối
    const p1Capacity = columnMode === 2 ? 1400 : 700;
    const pnCapacity = columnMode === 2 ? 1680 : 840;

    const result: { pageIndex: number; items: typeof annotatedQuestions }[] = [];
    let currentPageItems: typeof annotatedQuestions = [];
    let currentHeight = 0;

    for (let i = 0; i < annotatedQuestions.length; i++) {
      const item = annotatedQuestions[i];

      let weight = 0;
      if (item.isFirstOfPart) weight += 45;

      const stemChars = item.stem ? item.stem.length : 40;
      const stemLines = Math.ceil(stemChars / (columnMode === 2 ? 38 : 75));
      weight += stemLines * (density === 'compact' ? 17 : density === 'spacious' ? 24 : 20);

      if (item.tikz_code) weight += 150;

      if (item.type === 'MULTIPLE_CHOICE') {
        const grid = getChoiceGridClass(item.choices, choiceLayout);
        if (grid === 'grid-cols-4') {
          weight += (density === 'compact' ? 22 : 28);
        } else if (grid === 'grid-cols-2') {
          weight += (density === 'compact' ? 42 : 54);
        } else {
          weight += (density === 'compact' ? 82 : 105);
        }
      } else if (item.type === 'TRUE_FALSE') {
        weight += (item.statements?.length || 4) * (density === 'compact' ? 18 : 22);
      } else if (item.type === 'SHORT_ANSWER') {
        weight += (density === 'compact' ? 22 : 28);
      } else {
        weight += 50;
      }

      weight += (density === 'compact' ? 10 : density === 'spacious' ? 20 : 14);

      const maxCap = result.length === 0 ? p1Capacity : pnCapacity;

      if (currentPageItems.length > 0 && currentHeight + weight > maxCap) {
        result.push({ pageIndex: result.length + 1, items: currentPageItems });
        currentPageItems = [item];
        currentHeight = weight;
      } else {
        currentPageItems.push(item);
        currentHeight += weight;
      }
    }

    if (currentPageItems.length > 0) {
      result.push({ pageIndex: result.length + 1, items: currentPageItems });
    }

    return result;
  }, [annotatedQuestions, columnMode, choiceLayout, density]);

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
          {/* Nút Sinh toàn bộ đề */}
          <button
            onClick={onGenerateAll}
            disabled={isGeneratingAll}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition-colors duration-150 disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 text-amber-300 ${isGeneratingAll ? 'animate-spin' : ''}`} />
            <span>{isGeneratingAll ? `Đang sinh (${progress.current}/${progress.total})…` : 'AI Sinh toàn bộ đề'}</span>
          </button>

          {/* Nút Xuất bản & Trộn đề */}
          <button
            onClick={onOpenExport}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-lg shadow-sm transition-colors duration-150"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-emerald-400" />
            <span>Xuất bản & Trộn đề</span>
          </button>
        </div>
      </div>

      {/* Progress Bar khi đang sinh */}
      {isGeneratingAll && (
        <div className="w-full bg-slate-200 h-1 shrink-0 overflow-hidden no-print">
          <div 
            className="bg-blue-600 h-full transition-all duration-300"
            style={{ width: `${(progress.current / (progress.total || 1)) * 100}%` }}
          />
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
            {questions.map((q, idx) => {
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
                      {q.type === "MULTIPLE_CHOICE" ? "TN 4 Lựa chọn" : q.type === "TRUE_FALSE" ? "Đúng / Sai" : "Trả lời ngắn"}
                    </span>
                  </div>

                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                    isSelected ? "bg-white/20 text-white" : levelBadges[q.level]?.color || "bg-slate-100"
                  }`}>
                    {levelBadges[q.level]?.label}
                  </span>
                </button>
              );
            })}
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
                { id: 1, label: `Phần I (${questions.filter(q => q.type === "MULTIPLE_CHOICE").length})` },
                { id: 2, label: `Phần II (${questions.filter(q => q.type === "TRUE_FALSE").length})` },
                { id: 3, label: `Phần III (${questions.filter(q => q.type === "SHORT_ANSWER").length})` },
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
          <div className="flex-1 overflow-y-auto p-4">
            {filteredQuestions.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                <Sparkles className="w-10 h-10 text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-slate-600">Chưa có câu hỏi nào</p>
                <p className="text-xs text-slate-400 mt-1">Bấm "AI Sinh toàn bộ đề" ở thanh trên để bắt đầu.</p>
              </div>
            ) : (
              filteredQuestions.map((q, idx) => (
                <QuestionCard
                  key={q.id || idx}
                  question={q}
                  index={idx}
                  isActive={activeQuestionIndex === idx}
                  onRegenerate={(prompt) => onRegenerateSlot(q.id, prompt)}
                  onCloneNumbers={() => onCloneNumbers(q.id)}
                  onUpdate={onUpdateQuestion}
                />
              ))
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

              <button
                onClick={() => startTransition(() => setRightTab('pdf'))}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  rightTab === 'pdf' 
                    ? "bg-white text-blue-700 shadow-xs font-bold" 
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Biên dịch PDF</span>
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
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-lg shadow-xs transition cursor-pointer"
                  title="Tự động tính toán số câu, phương án và phân bổ vừa khít số trang A4 chuẩn"
                >
                  <Wand2 className="w-3.5 h-3.5 text-amber-100" />
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
              <div className="flex-1 overflow-y-auto p-4 flex flex-col items-center gap-6">
                {paginatedPages.length === 0 ? (
                  <div className="bg-white p-8 rounded-lg shadow-sm text-center text-slate-400 text-xs">
                    Chưa có câu hỏi nào để hiển thị.
                  </div>
                ) : (
                  paginatedPages.map((page) => {
                    const isFirstPage = page.pageIndex === 1;
                    const isLastPage = page.pageIndex === paginatedPages.length;

                    return (
                      <div
                        key={page.pageIndex}
                        className={`a4-sheet w-full ${isPreviewExpanded ? "max-w-[760px] p-8" : "max-w-[480px] xl:max-w-[540px] p-6"} text-slate-900 exam-paper-font flex flex-col justify-between`}
                        style={{ minHeight: isPreviewExpanded ? '1070px' : '720px' }}
                      >
                        <div>
                          {/* HEADER TRANG 1 (Chuẩn Bộ Giáo Dục & Đào Tạo) */}
                          {isFirstPage ? (
                            <div className="border-b border-slate-900 pb-3 mb-4">
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
                            <div className="flex justify-between items-center text-[10px] text-slate-500 border-b border-slate-300 pb-1.5 mb-4">
                              <span className="font-medium uppercase tracking-wide">
                                {matrix.title} • Mã đề: {examMeta.exam_code}
                              </span>
                              <span className="italic">
                                Trang {page.pageIndex}/{paginatedPages.length}
                              </span>
                            </div>
                          )}

                          {/* DANH SÁCH CÂU HỎI TRONG TRANG */}
                          <div className={columnMode === 2 ? "two-column-exam" : (density === 'compact' ? "space-y-2.5" : density === 'spacious' ? "space-y-4" : "space-y-3")}>
                            {page.items.map((q) => {
                              const choiceGrid = getChoiceGridClass(q.choices, choiceLayout);

                              return (
                                <div key={q.id || q.globalIndex} className="question-avoid-break mb-3">
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

                                    {/* Hình vẽ TikZ (nếu có) */}
                                    {q.tikz_code && q.tikz_code.trim() && (
                                      <div className="my-1.5 p-2 bg-slate-50 border border-slate-200 rounded text-center text-[10px] text-slate-500 italic">
                                        [Hình vẽ TikZ / Bảng biến thiên]
                                      </div>
                                    )}

                                    {/* Phương án trắc nghiệm 4 lựa chọn (Phần I) */}
                                    {q.type === "MULTIPLE_CHOICE" && q.choices && (
                                      <div className={`grid ${choiceGrid} gap-x-2 gap-y-1 pl-3 pt-0.5 font-sans text-[11px]`}>
                                        {q.choices.map((c, i) => (
                                          <div key={i} className="flex items-start gap-1">
                                            <span className="font-bold shrink-0">{["A", "B", "C", "D"][i]}.</span>
                                            <div className="truncate flex-1">
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
                        <div className="border-t border-slate-300 pt-2 mt-4 text-center text-[10px] text-slate-500">
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
                  <span className="font-mono text-emerald-400">ex_test.sty format (Chuẩn 2026)</span>
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
                  className="flex-1 w-full bg-slate-900 text-emerald-300 font-mono text-[11px] p-3 rounded-lg border border-slate-800 focus:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500 resize-none overflow-y-auto leading-relaxed select-all"
                />
              </div>
            </ViewTransition>
          )}

          {/* Tab 3: Compiled PDF View */}
          {rightTab === 'pdf' && (
            <ViewTransition enter="fade-in" exit="fade-out">
              <div className="flex-1 p-6 bg-slate-50 flex flex-col items-center justify-center text-center">
                <Printer className="w-12 h-12 text-blue-600 mb-3" />
                <h3 className="font-bold text-slate-800 text-base mb-1">Biên dịch PDF bằng TeX Live</h3>
                <p className="text-xs text-slate-500 max-w-xs mb-5 leading-relaxed">
                  Biên dịch mã nguồn LaTeX qua container Docker TeX Live hoặc pdflatex để xuất file PDF in ấn chuẩn A4.
                </p>

                <button
                  onClick={onCompilePdf}
                  disabled={isCompiling}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md transition disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <Printer className={`w-4 h-4 ${isCompiling ? 'animate-spin' : ''}`} />
                  <span>{isCompiling ? 'Đang biên dịch PDF…' : 'Tiến hành biên dịch PDF ngay'}</span>
                </button>
              </div>
            </ViewTransition>
          )}
        </aside>
      </div>
    </div>
  );
};
