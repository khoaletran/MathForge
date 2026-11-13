import React, { useState, useEffect, useLayoutEffect, useRef, useCallback } from 'react';
import { 
  Sparkles, Layers, Settings, SlidersHorizontal, 
  FileText, CheckCircle, ArrowRight, ArrowLeft, Plus,
  LayoutDashboard, Library, TableProperties, Wand2, 
  ChevronRight, FileDown, Upload, RefreshCw, Download, Pencil 
} from 'lucide-react';
import { Question } from './components/QuestionCard';
import { ExamMatrix } from './components/MatrixManager';
import { Dashboard } from './components/Dashboard';
import { GradeMatrixPicker } from './components/GradeMatrixPicker';
import { MatrixManager } from './components/MatrixManager';
import { ExamStudio } from './components/ExamStudio';
import { ExportModal } from './components/ExportModal';
import { CreateMatrixModal } from './components/CreateMatrixModal';
import { SettingsModal } from './components/SettingsModal';

type NavMenu = 'dashboard' | 'grade_picker' | 'matrix_builder' | 'studio';

const DRAFT_KEY = 'math-exam-draft-v1';
const DEFAULT_EXAM_META = {
  school_name: "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
  exam_name: "KỲ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG NĂM 2025",
  academic_year: "2024 - 2025",
  exam_code: "101",
};

type ReferenceSource = { title: string; url: string };

type ExamDraft = {
  referenceSources?: ReferenceSource[];
  matrix: ExamMatrix;
  questions: Question[];
  examMeta: typeof DEFAULT_EXAM_META;
  activeMenu: NavMenu;
  includeSolution: boolean;
};

function readExamDraft(): ExamDraft | null {
  try {
    const stored = sessionStorage.getItem(DRAFT_KEY);
    if (!stored) return null;
    const draft = JSON.parse(stored) as ExamDraft;
    if (!Array.isArray(draft?.matrix?.slots) || !Array.isArray(draft.questions)) return null;
    if (!Object.keys(DEFAULT_EXAM_META).every(key =>
      typeof draft.examMeta?.[key as keyof typeof DEFAULT_EXAM_META] === 'string'
    )) return null;
    return draft;
  } catch {
    return null;
  }
}

export function App() {
  const [draft] = useState(readExamDraft);
  const [activeMenu, setActiveMenu] = useState<NavMenu>(draft?.activeMenu ?? 'dashboard');
  const [matrix, setMatrix] = useState<ExamMatrix | null>(draft?.matrix ?? null);
  const [referenceSources, setReferenceSources] = useState<ReferenceSource[]>(draft?.referenceSources ?? []);
  const [questions, setQuestions] = useState<Question[]>(draft?.questions ?? []);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [examMeta, setExamMeta] = useState(draft?.examMeta ?? DEFAULT_EXAM_META);
  const [docxLayout, setDocxLayout] = useState<{ choice_layout: 'auto' | '4col' | '2col' | '1col'; density: 'compact' | 'normal' | 'spacious'; font_size: 'sm' | 'base' | 'lg'; column_mode: 1 | 2 }>({ choice_layout: 'auto', density: 'normal', font_size: 'sm', column_mode: 1 });
  const handleLayoutChange = useCallback((layout: typeof docxLayout) => setDocxLayout(layout), []);

  // Modals state
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isCreateMatrixOpen, setIsCreateMatrixOpen] = useState(false);
  const [latexCode, setLatexCode] = useState('');
  const [includeSolution, setIncludeSolution] = useState(draft?.includeSolution ?? true);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('GEMINI_API_KEY') || '');
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const generationTokenRef = useRef(0);
  const latexTokenRef = useRef(0);
  const topFileInputRef = useRef<HTMLInputElement>(null);

  const handleTopFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && matrix) {
      await handleUploadExcel(e.target.files[0], matrix.grade);
    }
  };

  const handleRenameExam = () => {
    if (!matrix) return;
    const newTitle = window.prompt("Nhập tên mới cho đề thi:", matrix.title);
    if (newTitle && newTitle.trim()) {
      setMatrix({ ...matrix, title: newTitle.trim() });
      setExamMeta(prev => ({ ...prev, exam_name: newTitle.trim() }));
      showToast("Đã cập nhật tên đề thi.");
    }
  };

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  useEffect(() => {
    fetchHealth();
    if (!draft) fetchDefaultMatrix();
  }, []);

  useLayoutEffect(() => {
    if (!matrix) return;
    try {
      const snapshot: ExamDraft = { matrix, questions, examMeta, activeMenu, includeSolution, referenceSources };
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(snapshot));
    } catch {
      // The editor remains usable if browser storage is unavailable.
    }
  }, [matrix, questions, examMeta, activeMenu, includeSolution, referenceSources]);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      }
    } catch (e) {
      console.warn("Chưa kết nối được với Backend:", e);
    }
  };

  const fetchDefaultMatrix = async () => {
    const token = generationTokenRef.current;
    try {
      const res = await fetch('/api/matrix/default');
      if (res.ok) {
        const data: ExamMatrix = await res.json();
        if (generationTokenRef.current !== token) return;
        setMatrix(data);
      }
    } catch (e) {
      showToast("Không thể tải ma trận mặc định.");
    }
  };

  const replaceMatrix = (selectedMatrix: ExamMatrix) => {
    generationTokenRef.current++;
    latexTokenRef.current++;
    setMatrix(selectedMatrix);
    setQuestions([]);
    setReferenceSources([]);
    setLatexCode('');
    setIsGeneratingAll(false);
  };

  const handleSelectMatrix = async (selectedMatrix: ExamMatrix, autoGenerate: boolean = false) => {
    replaceMatrix(selectedMatrix);
    setExamMeta(prev => ({
      ...prev,
      exam_name: selectedMatrix.title
    }));

    if (autoGenerate) {
      setActiveMenu('studio');
      handleGenerateAllWithMatrix(selectedMatrix);
    } else {
      setActiveMenu('matrix_builder');
      showToast(`Đã chọn ma trận: ${selectedMatrix.title}`);
    }
  };

  const handleSelectPreset = async (matrixId: string) => {
    try {
      const res = await fetch(`/api/matrix/${matrixId}`);
      if (res.ok) {
        const m: ExamMatrix = await res.json();
        handleSelectMatrix(m, true);
      }
    } catch (e) {
      showToast("Không thể nạp ma trận mẫu.");
    }
  };

  const requestExam = async (targetMatrix: ExamMatrix) => {
    const res = await fetch('/api/generate/exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...examMeta,
        exam_name: targetMatrix.title,
        matrix: targetMatrix,
        search_references: true,
        api_key: apiKey || undefined,
      }),
    });
    const result = await res.json();
    if (!res.ok) {
      throw new Error(typeof result.detail === 'string' ? result.detail : 'Không thể sinh đề theo ma trận.');
    }
    if (result.questions.length !== targetMatrix.slots.length ||
        result.questions.some((question: Question, i: number) => question.id !== targetMatrix.slots[i].slot_id)) {
      throw new Error('Kết quả sinh đề thiếu câu hoặc sai thứ tự ma trận.');
    }
    return result as { questions: Question[]; reference_sources?: ReferenceSource[] };
  };

  const handleGenerateAllWithMatrix = async (targetMatrix: ExamMatrix) => {
    setIsGeneratingAll(true);
    const token = ++generationTokenRef.current;
    try {
      const result = await requestExam(targetMatrix);
      const generated = result.questions;
      if (generationTokenRef.current !== token) return;
      setQuestions(generated);
      setReferenceSources(result.reference_sources ?? []);
      setLatexCode('');
      void refreshLatexCode(targetMatrix, generated);
      showToast(result.reference_sources?.length
        ? `Đã sinh ${generated.length} câu. Có nguồn đề tham khảo.`
        : `Đã sinh ${generated.length} câu. Không có nguồn web phù hợp hoặc tìm kiếm không khả dụng.`);
    } catch (e) {
      if (generationTokenRef.current === token) {
        showToast(e instanceof Error ? e.message : 'Không thể sinh đề theo ma trận.');
      }
    } finally {
      if (generationTokenRef.current === token) setIsGeneratingAll(false);
    }
  };

  const handleGenerateAll = async () => {
    if (!matrix) return;
    await handleGenerateAllWithMatrix(matrix);
  };

  const replaceQuestion = async (slotId: string, mode: "regenerate" | "clone", customPrompt?: string) => {
    if (!matrix || isGeneratingAll) return;
    const targetSlot = matrix.slots.find(s => s.slot_id === slotId);
    if (!targetSlot) {
      showToast(`Không tìm thấy ô ma trận #${slotId} trong ma trận hiện tại!`);
      return;
    }

    const currentQ = questions.find(q => q.id === slotId);
    if (!currentQ) return;
    const token = ++generationTokenRef.current;
    const otherQuestions = questions.filter(q => q.id !== slotId);

    try {
      const res = await fetch('/api/generate/slot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slot: targetSlot,
          grade: matrix.grade,
          avoid_questions: otherQuestions,
          original_question: currentQ,
          mode,
          custom_prompt: customPrompt,
          api_key: apiKey || undefined
        })
      });
      const result = await res.json();
      if (generationTokenRef.current !== token) return;
      if (res.ok) {
        const newQ: Question = result;
        const updated = questions.map(q => q.id === slotId ? newQ : q);
        setQuestions(updated);
        setLatexCode('');
        void refreshLatexCode(matrix, updated);
        showToast(mode === "clone" ? "Đã đổi số liệu." : "Đã đổi câu hỏi.");
      } else {
        showToast(result.detail || "Không thể đổi câu hỏi lúc này.");
      }
    } catch (e) {
      if (generationTokenRef.current === token) showToast("Không thể đổi câu hỏi lúc này.");
    }
  };

  const handleRegenerateSlot = (slotId: string, customPrompt?: string) =>
    replaceQuestion(slotId, "regenerate", customPrompt);

  const handleCloneNumbers = (slotId: string) => replaceQuestion(slotId, "clone");

  const handleUpdateQuestion = (updatedQ: Question) => {
    if (isGeneratingAll) return;
    generationTokenRef.current++;
    const updated = questions.map(q => q.id === updatedQ.id ? updatedQ : q);
    setQuestions(updated);
    if (matrix) refreshLatexCode(matrix, updated);
    showToast("Đã lưu chỉnh sửa câu hỏi.");
  };

  const refreshLatexCode = async (currentM: ExamMatrix, currentQs: Question[]) => {
    const token = ++latexTokenRef.current;
    try {
      const paper = {
        id: `exam_${examMeta.exam_code}`,
        title: currentM.title,
        school_name: examMeta.school_name,
        exam_name: examMeta.exam_name,
        academic_year: examMeta.academic_year,
        exam_code: examMeta.exam_code,
        time_minutes: currentM.time_minutes,
        questions: currentQs
      };

      const res = await fetch('/api/export/latex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper, include_solution: includeSolution })
      });

      if (res.ok) {
        const data = await res.json();
        if (latexTokenRef.current === token) setLatexCode(data.latex_code);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleOpenExport = async () => {
    if (matrix) {
      await refreshLatexCode(matrix, questions);
    }
    setIsExportOpen(true);
  };

  const handleDownloadDocx = async () => {
    if (!matrix || questions.length === 0) return;
    try {
      const paper = {
        id: `exam_${examMeta.exam_code}`,
        title: matrix.title,
        ...examMeta,
        time_minutes: matrix.time_minutes,
        questions,
      };
      const response = await fetch('/api/export/docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper, include_solution: includeSolution, ...docxLayout }),
      });
      if (!response.ok) throw new Error('Không thể tạo file DOCX.');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url;
      link.download = `De_thi_Toan_${examMeta.exam_code}.docx`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Không thể tải DOCX.');
    }
  };

  const handleSavePdf = () => {
    setIsExportOpen(false);
    setTimeout(() => window.print(), 100);
  };

  const handleUploadExcel = async (file: File, grade?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (grade) {
      formData.append('grade', String(grade));
    }
    try {
      const res = await fetch('/api/matrix/upload-excel', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const newMatrix: ExamMatrix = await res.json();
        replaceMatrix(newMatrix);
        setActiveMenu('matrix_builder');
        showToast(`Đã nạp thành công ma trận gồm ${newMatrix.slots.length} câu từ file Excel (Lớp ${newMatrix.grade})!`);
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || "Lỗi khi đọc file Excel.");
      }
    } catch (e: any) {
      showToast(e.message || "Không thể tải lên file.");
    }
  };

  const handleSaveCustomMatrix = async (newMatrix: ExamMatrix) => {
    try {
      const res = await fetch('/api/matrix/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMatrix)
      });
      if (res.ok) {
        const saved: ExamMatrix = await res.json();
        replaceMatrix(saved);
        setActiveMenu('matrix_builder');
        showToast("Đã lưu ma trận mới thành công!");
      }
    } catch (e) {
      showToast("Không thể lưu ma trận.");
    }
  };

  const navigateTo = (menu: NavMenu) => {
    if (activeMenu === menu) return;
    setActiveMenu(menu);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* Toast Notification */}
      {notification && (
        <div 
          role="status" 
          aria-live="polite"
          className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 text-xs md:text-sm animate-in slide-in-from-bottom-5"
        >
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          <span>{notification}</span>
        </div>
      )}

      {/* ADAPTIVE TOP NAVIGATION BAR (Fixed h-14, 2-Mode Header) */}
      <header className="h-14 bg-white/90 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-50 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between gap-3">
          {/* ========================================================= */}
          {/* CHẾ ĐỘ A: WORKSPACE MODE (Dashboard hoặc Grade Picker)   */}
          {/* ========================================================= */}
          {(activeMenu === 'dashboard' || activeMenu === 'grade_picker') && (
            <>
              {/* Cụm Trái: Brand Identity */}
              <button
                type="button"
                onClick={() => navigateTo('dashboard')}
                className="flex items-center gap-2.5 cursor-pointer text-left bg-transparent border-0 p-0 focus:outline-none rounded-lg shrink-0 group"
                aria-label="Về không gian làm việc"
              >
                <img src="/logo.png" alt="" width={36} height={36}
                  className="h-9 w-9 rounded-lg object-contain" />
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 text-sm md:text-base leading-none">
                    MathForge
                  </span>
                </div>
              </button>

              {/* Cụm Giữa: Segmented Navigation (2 tab chính) */}
              <nav className="inline-flex p-1 bg-slate-100 rounded-xl text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => navigateTo('dashboard')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors duration-150 ${
                    activeMenu === 'dashboard'
                      ? "bg-white text-blue-700 shadow-xs font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4 stroke-[1.75]" />
                  <span>Không gian làm việc</span>
                </button>

                <button
                  type="button"
                  onClick={() => navigateTo('grade_picker')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors duration-150 ${
                    activeMenu === 'grade_picker'
                      ? "bg-white text-blue-700 shadow-xs font-bold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Library className="w-4 h-4 stroke-[1.75]" />
                  <span>Kho Ma trận theo Lớp</span>
                </button>
              </nav>

              {/* Cụm Phải: Global Actions (Resume, Tạo đề mới, Cài đặt) */}
              <div className="flex items-center gap-2 shrink-0">
                {matrix && (
                  <button
                    type="button"
                    onClick={() => navigateTo(questions.length > 0 ? 'studio' : 'matrix_builder')}
                    className="hidden lg:inline-flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/80 rounded-xl text-xs font-semibold text-slate-700 transition-colors"
                    title={matrix.title}
                  >
                    <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                    <span className="max-w-[150px] truncate">
                      Tiếp tục: {matrix.title}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 stroke-[1.75] text-slate-400" />
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => setIsCreateMatrixOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors"
                >
                  <Plus className="w-4 h-4 stroke-[1.75]" />
                  <span>Tạo đề mới</span>
                </button>

                <button
                  type="button"
                  onClick={() => setIsSettingsOpen(true)}
                  aria-label="Cài đặt hệ thống và API key"
                  className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Cấu hình Gemini API & Chẩn đoán hệ thống"
                >
                  <Settings className="w-4 h-4 stroke-[1.75]" />
                </button>
              </div>
            </>
          )}

          {/* ========================================================= */}
          {/* CHẾ ĐỘ B: ACTIVE EXAM WORKFLOW MODE (Matrix hoặc Studio) */}
          {/* ========================================================= */}
          {(activeMenu === 'matrix_builder' || activeMenu === 'studio') && (
            <>
              {/* Cụm Trái: Back & Context */}
              <div className="flex items-center gap-1 shrink-0 min-w-0">
                <button
                  type="button"
                  onClick={() => navigateTo('dashboard')}
                  className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors"
                  title="Quay về Không gian làm việc"
                >
                  <ArrowLeft className="w-4 h-4 stroke-[1.75]" />
                </button>

                <div className="h-5 w-[1px] bg-slate-200 mx-1.5" />

                <div className="flex items-center gap-2 min-w-0">
                  <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[11px] font-bold rounded-md border border-blue-200/70 shrink-0">
                    Lớp {matrix?.grade || 12}
                  </span>
                  <span className="font-semibold text-slate-900 text-xs md:text-sm truncate max-w-[140px] sm:max-w-[200px] md:max-w-[260px]">
                    {matrix?.title || "Đề thi mới"}
                  </span>
                  <button
                    type="button"
                    onClick={handleRenameExam}
                    className="p-1 text-slate-400 hover:text-slate-700 rounded transition-colors"
                    title="Đổi tên đề thi"
                  >
                    <Pencil className="w-3.5 h-3.5 stroke-[1.75]" />
                  </button>
                </div>
              </div>

              {/* Cụm Giữa: Connected Workflow Stepper */}
              <nav className="hidden sm:inline-flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => navigateTo('matrix_builder')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                    activeMenu === 'matrix_builder'
                      ? "bg-blue-600 text-white shadow-xs font-bold"
                      : "text-slate-600 hover:bg-slate-200/80"
                  }`}
                >
                  <TableProperties className="w-4 h-4 stroke-[1.75]" />
                  <span>1. Ma trận đặc tả</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold tabular-nums ${
                    activeMenu === 'matrix_builder' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {matrix?.slots?.length || 0} câu • {(matrix?.slots?.reduce((sum, s) => sum + (Number(s.points) || 0), 0) || 10).toFixed(1)}đ
                  </span>
                </button>

                <ChevronRight className="w-3.5 h-3.5 stroke-[1.75] text-slate-400 shrink-0" />

                <button
                  type="button"
                  onClick={() => navigateTo('studio')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                    activeMenu === 'studio'
                      ? "bg-blue-600 text-white shadow-xs font-bold"
                      : "text-slate-600 hover:bg-slate-200/80"
                  }`}
                >
                  <Wand2 className="w-4 h-4 stroke-[1.75]" />
                  <span>2. Phòng Soạn Đề</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold tabular-nums ${
                    activeMenu === 'studio' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {questions.length}/{matrix?.slots?.length || 0}
                  </span>
                </button>
              </nav>

              {/* Cụm Phải: Contextual Actions theo Step */}
              <div className="flex items-center gap-2 shrink-0">
                {activeMenu === 'matrix_builder' && (
                  <>
                    <button
                      type="button"
                      onClick={() => matrix && window.open(`/api/matrix/download-template?matrix_id=${matrix.id}`, '_blank')}
                      className="hidden md:inline-flex items-center gap-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
                      title="Tải mẫu Excel ma trận này"
                    >
                      <FileDown className="w-4 h-4 stroke-[1.75]" />
                      <span>Tải mẫu Excel</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => topFileInputRef.current?.click()}
                      className="hidden md:inline-flex items-center gap-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
                      title="Nhập file Excel"
                    >
                      <Upload className="w-4 h-4 stroke-[1.75]" />
                      <span>Nhập Excel</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        if (!matrix) return;
                        navigateTo('studio');
                        handleGenerateAllWithMatrix(matrix);
                      }}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors"
                    >
                      <Sparkles className="w-4 h-4 stroke-[1.75]" />
                      <span>Sinh đề ngay</span>
                      <ArrowRight className="w-3.5 h-3.5 stroke-[1.75]" />
                    </button>
                  </>
                )}

                {activeMenu === 'studio' && (
                  <>
                    <button
                      type="button"
                      onClick={handleGenerateAll}
                      disabled={isGeneratingAll}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors disabled:opacity-50"
                      title="AI sinh lại toàn bộ câu hỏi"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 stroke-[1.75] ${isGeneratingAll ? 'animate-spin' : ''}`} />
                      <span className="hidden sm:inline">AI Sinh lại bộ đề</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleOpenExport}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-xs transition-colors"
                    >
                      <Download className="w-4 h-4 stroke-[1.75] text-emerald-400" />
                      <span>Xuất bản & Trộn đề</span>
                    </button>
                  </>
                )}
              </div>
            </>
          )}
        </div>

        {/* Input file ẩn cho nút Nhập Excel ở Topbar */}
        <input
          type="file"
          ref={topFileInputRef}
          onChange={handleTopFileChange}
          accept=".xlsx,.xls"
          className="hidden"
          aria-label="Tải lên file Excel ma trận từ thanh điều hướng"
        />
      </header>

      {/* MAIN VIEW CONTENT CONTAINER WITH CLEAN ENTER-ONLY TRANSITION */}
      <main key={activeMenu} className="flex-1 flex flex-col">
        {activeMenu === 'dashboard' ? (
          <div className="max-w-6xl mx-auto px-4 py-8 w-full animate-tab-enter">
            <Dashboard
              onNavigateToGradePicker={() => navigateTo('grade_picker')}
              onNavigateToMatrixManager={() => navigateTo('matrix_builder')}
              onOpenCreateMatrix={() => setIsCreateMatrixOpen(true)}
              onUploadExcel={handleUploadExcel}
              onSelectPreset={handleSelectPreset}
              currentMatrix={matrix}
              onGoToStudio={() => navigateTo('studio')}
            />
          </div>
        ) : activeMenu === 'grade_picker' ? (
          <div className="max-w-6xl mx-auto px-4 py-8 w-full animate-tab-enter">
            <GradeMatrixPicker
              onSelectMatrix={handleSelectMatrix}
              onOpenCreateMatrix={() => setIsCreateMatrixOpen(true)}
              onUploadExcel={handleUploadExcel}
            />
          </div>
        ) : activeMenu === 'matrix_builder' && matrix ? (
          <div className="max-w-6xl mx-auto px-4 py-8 w-full animate-tab-enter">
            <MatrixManager
              matrix={matrix}
              onUpdateMatrix={replaceMatrix}
              onUploadExcel={handleUploadExcel}
              onDownloadTemplate={() => window.open(`/api/matrix/download-template?matrix_id=${matrix.id}`, '_blank')}
              onStartGenerate={() => {
                navigateTo('studio');
                handleGenerateAllWithMatrix(matrix);
              }}
              onOpenCreateMatrix={() => setIsCreateMatrixOpen(true)}
            />
          </div>
        ) : activeMenu === 'studio' && matrix ? (
          <div className="flex-1 flex flex-col w-full h-full animate-tab-enter">
            <ExamStudio
              onLayoutChange={handleLayoutChange}
              includeSolution={includeSolution}
              referenceSources={referenceSources}
              matrix={matrix}
              questions={questions}
              examMeta={examMeta}
              onGenerateAll={handleGenerateAll}
              isGeneratingAll={isGeneratingAll}
              onRegenerateSlot={handleRegenerateSlot}
              onCloneNumbers={handleCloneNumbers}
              onUpdateQuestion={handleUpdateQuestion}
              onOpenExport={handleOpenExport}
              latexCode={latexCode}
            />
          </div>
        ) : null}
      </main>

      {/* Modals */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        latexCode={latexCode}
        onDownloadDocx={handleDownloadDocx}
        onSavePdf={handleSavePdf}
        includeSolution={includeSolution}
        onToggleSolution={setIncludeSolution}
        examMeta={examMeta}
        onUpdateExamMeta={setExamMeta}
        questions={questions}
      />

      <CreateMatrixModal
        isOpen={isCreateMatrixOpen}
        onClose={() => setIsCreateMatrixOpen(false)}
        onSave={handleSaveCustomMatrix}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiKey={apiKey}
        onSaveApiKey={(key) => {
          setApiKey(key);
          localStorage.setItem('GEMINI_API_KEY', key);
        }}
        systemHealth={systemHealth}
      />
    </div>
  );
}

export default App;
