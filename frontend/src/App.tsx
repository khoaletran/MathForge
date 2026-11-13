import React, { useState, useEffect, startTransition, ViewTransition } from 'react';
import { 
  Sparkles, Layers, BookOpen, Settings, SlidersHorizontal, 
  FileText, CheckCircle, ArrowRight, GraduationCap, Home, Code, Printer 
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

export function App() {
  const [activeMenu, setActiveMenu] = useState<NavMenu>('dashboard');
  const [matrix, setMatrix] = useState<ExamMatrix | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  // Metadata đề thi
  const [examMeta, setExamMeta] = useState({
    school_name: "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
    exam_name: "KỲ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG NĂM 2025",
    academic_year: "2024 - 2025",
    exam_code: "101"
  });

  // Modals state
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isCreateMatrixOpen, setIsCreateMatrixOpen] = useState(false);
  const [latexCode, setLatexCode] = useState('');
  const [includeSolution, setIncludeSolution] = useState(true);
  const [isCompiling, setIsCompiling] = useState(false);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('GEMINI_API_KEY') || '');
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  useEffect(() => {
    fetchHealth();
    fetchDefaultMatrix();
  }, []);

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
    try {
      const res = await fetch('/api/matrix/default');
      if (res.ok) {
        const data: ExamMatrix = await res.json();
        setMatrix(data);
        generateInitialSample(data);
      }
    } catch (e) {
      showToast("Không thể tải ma trận mặc định.");
    }
  };

  const generateInitialSample = async (mat: ExamMatrix) => {
    try {
      const initialSlots = [mat.slots[0], mat.slots[12], mat.slots[16]];
      const promises = initialSlots.map(slot => 
        fetch('/api/generate/slot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slot, api_key: apiKey || undefined })
        }).then(r => r.json())
      );
      const results = await Promise.all(promises);
      setQuestions(results);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectMatrix = async (selectedMatrix: ExamMatrix, autoGenerate: boolean = false) => {
    setMatrix(selectedMatrix);
    setExamMeta(prev => ({
      ...prev,
      exam_name: selectedMatrix.title
    }));

    if (autoGenerate) {
      setActiveMenu('studio');
      // Tự động sinh câu hỏi
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

  const handleGenerateAllWithMatrix = async (targetMatrix: ExamMatrix) => {
    setIsGeneratingAll(true);
    setProgress({ current: 0, total: targetMatrix.slots.length });

    const newQuestions: Question[] = [];
    try {
      for (let i = 0; i < targetMatrix.slots.length; i++) {
        const slot = targetMatrix.slots[i];
        setProgress({ current: i + 1, total: targetMatrix.slots.length });
        
        const res = await fetch('/api/generate/slot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slot, api_key: apiKey || undefined })
        });
        
        if (res.ok) {
          const q: Question = await res.json();
          newQuestions.push(q);
          setQuestions([...newQuestions]);
        }
      }
      showToast("Đã sinh toàn bộ đề thi thành công theo ma trận!");
      refreshLatexCode(targetMatrix, newQuestions);
    } catch (e) {
      showToast("Có lỗi xảy ra trong quá trình sinh đề.");
    } finally {
      setIsGeneratingAll(false);
    }
  };

  const handleGenerateAll = async () => {
    if (!matrix) return;
    await handleGenerateAllWithMatrix(matrix);
  };

  const handleRegenerateSlot = async (slotId: string, customPrompt?: string) => {
    if (!matrix) return;
    const targetSlot = matrix.slots.find(s => s.slot_id === slotId) || matrix.slots[0];
    try {
      const res = await fetch('/api/generate/slot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slot: targetSlot,
          custom_prompt: customPrompt,
          api_key: apiKey || undefined
        })
      });
      if (res.ok) {
        const newQ: Question = await res.json();
        const updated = questions.map(q => q.id === slotId ? newQ : q);
        setQuestions(updated);
        refreshLatexCode(matrix, updated);
        showToast("Đã đổi câu hỏi thành công!");
      }
    } catch (e) {
      showToast("Không thể đổi câu hỏi lúc này.");
    }
  };

  const handleCloneNumbers = async (slotId: string) => {
    await handleRegenerateSlot(slotId, "Giữ nguyên dạng bài toán, chỉ thay đổi số liệu/hàm số và tự tính lại đáp án.");
  };

  const handleUpdateQuestion = (updatedQ: Question) => {
    const updated = questions.map(q => q.id === updatedQ.id ? updatedQ : q);
    setQuestions(updated);
    if (matrix) refreshLatexCode(matrix, updated);
    showToast("Đã lưu chỉnh sửa câu hỏi.");
  };

  const refreshLatexCode = async (currentM: ExamMatrix, currentQs: Question[]) => {
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
        setLatexCode(data.latex_code);
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

  const handleCompilePdf = async () => {
    if (!matrix) return;
    setIsCompiling(true);
    try {
      const paper = {
        id: `exam_${examMeta.exam_code}`,
        title: matrix.title,
        school_name: examMeta.school_name,
        exam_name: examMeta.exam_name,
        academic_year: examMeta.academic_year,
        exam_code: examMeta.exam_code,
        time_minutes: matrix.time_minutes,
        questions: questions
      };

      const res = await fetch('/api/export/compile-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper, include_solution: includeSolution })
      });

      if (res.ok) {
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/pdf")) {
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `De_thi_Toan_${examMeta.exam_code}.pdf`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          showToast("Đã biên dịch và tải về file PDF thành công!");
        } else {
          const data = await res.json();
          alert(data.message || "Chưa thể biên dịch trực tiếp PDF.");
        }
      }
    } catch (e) {
      showToast("Lỗi khi kết nối trình biên dịch.");
    } finally {
      setIsCompiling(false);
    }
  };

  const handleUploadExcel = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/matrix/upload-excel', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const newMatrix: ExamMatrix = await res.json();
        setMatrix(newMatrix);
        setActiveMenu('matrix_builder');
        showToast(`Đã nạp thành công ma trận gồm ${newMatrix.slots.length} câu từ file Excel!`);
      } else {
        showToast("Lỗi khi đọc file Excel.");
      }
    } catch (e) {
      showToast("Không thể tải lên file.");
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
        setMatrix(saved);
        setActiveMenu('matrix_builder');
        showToast("Đã lưu ma trận mới thành công!");
      }
    } catch (e) {
      showToast("Không thể lưu ma trận.");
    }
  };

  const navigateTo = (menu: NavMenu) => {
    startTransition(() => {
      setActiveMenu(menu);
    });
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

      {/* TOP NAVIGATION BAR WITH COMPLETE MENU */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          {/* Logo & Brand */}
          <button 
            type="button"
            onClick={() => navigateTo('dashboard')}
            className="flex items-center gap-3 cursor-pointer shrink-0 text-left bg-transparent border-0 p-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-lg"
            aria-label="Về trang tổng quan"
          >
            <div className="w-10 h-10 bg-gradient-to-tr from-blue-700 to-indigo-600 rounded-xl flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-slate-900 text-base md:text-lg leading-none">
                  AI Math Exam Studio
                </span>
                <span className="text-[10px] bg-blue-50 text-blue-700 font-bold px-1.5 py-0.5 rounded border border-blue-200 hidden sm:inline">
                  ex_test.sty
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">
                Bộ GD&ĐT 2026 • GDPT 2018
              </p>
            </div>
          </button>

          {/* Central Main Menu Navigation */}
          <nav className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto">
            <button
              onClick={() => navigateTo('dashboard')}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs md:text-sm font-bold transition-colors duration-150 whitespace-nowrap focus-visible:ring-2 focus-visible:ring-blue-500 ${
                activeMenu === 'dashboard'
                  ? "bg-blue-50 text-blue-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Home className="w-4 h-4" />
              <span>Tổng quan</span>
            </button>

            <button
              onClick={() => navigateTo('grade_picker')}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs md:text-sm font-bold transition-colors duration-150 whitespace-nowrap focus-visible:ring-2 focus-visible:ring-blue-500 ${
                activeMenu === 'grade_picker'
                  ? "bg-blue-50 text-blue-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              <span>Tạo đề theo Lớp</span>
            </button>

            <button
              onClick={() => navigateTo('matrix_builder')}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs md:text-sm font-bold transition-colors duration-150 whitespace-nowrap focus-visible:ring-2 focus-visible:ring-blue-500 ${
                activeMenu === 'matrix_builder'
                  ? "bg-blue-50 text-blue-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Ma trận đặc tả</span>
            </button>

            <button
              onClick={() => navigateTo('studio')}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs md:text-sm font-bold transition-colors duration-150 whitespace-nowrap focus-visible:ring-2 focus-visible:ring-blue-500 ${
                activeMenu === 'studio'
                  ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs"
                  : "text-slate-700 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Phòng Soạn Đề (Studio)</span>
            </button>
          </nav>

          {/* Right Action Utilities */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleOpenExport}
              aria-label="Xuất đề thi và biên dịch"
              className="inline-flex items-center gap-1 px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-lg shadow-sm transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Xuất bản LaTeX và Biên dịch PDF"
            >
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden md:inline">Xuất đề</span>
            </button>

            <button
              onClick={() => setIsSettingsOpen(true)}
              aria-label="Cài đặt hệ thống và API key"
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Cấu hình Gemini API & Chẩn đoán hệ thống"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* MAIN VIEW CONTENT CONTAINER WITH REACT VIEW TRANSITIONS */}
      <main className="flex-1 flex flex-col">
        {/* VIEW 1: DASHBOARD */}
        {activeMenu === 'dashboard' && (
          <ViewTransition enter="fade-in" exit="fade-out">
            <div className="max-w-6xl mx-auto px-4 py-8 w-full">
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
          </ViewTransition>
        )}

        {/* VIEW 2: GRADE-BASED MATRIX PICKER */}
        {activeMenu === 'grade_picker' && (
          <ViewTransition enter="fade-in" exit="fade-out">
            <div className="max-w-6xl mx-auto px-4 py-8 w-full">
              <GradeMatrixPicker
                onSelectMatrix={handleSelectMatrix}
                onOpenCreateMatrix={() => setIsCreateMatrixOpen(true)}
                onUploadExcel={handleUploadExcel}
              />
            </div>
          </ViewTransition>
        )}

        {/* VIEW 3: MATRIX BUILDER & HUB */}
        {activeMenu === 'matrix_builder' && matrix && (
          <ViewTransition enter="fade-in" exit="fade-out">
            <div className="max-w-6xl mx-auto px-4 py-8 w-full">
              <MatrixManager
                matrix={matrix}
                onUpdateMatrix={setMatrix}
                onUploadExcel={handleUploadExcel}
                onDownloadTemplate={() => window.open(`/api/matrix/download-template?matrix_id=${matrix.id}`, '_blank')}
                onStartGenerate={() => {
                  navigateTo('studio');
                  handleGenerateAllWithMatrix(matrix);
                }}
                onOpenCreateMatrix={() => setIsCreateMatrixOpen(true)}
              />
            </div>
          </ViewTransition>
        )}

        {/* VIEW 4: AI EXAM STUDIO (3-PANE SPLIT LAYOUT) */}
        {activeMenu === 'studio' && matrix && (
          <ViewTransition enter="fade-in" exit="fade-out">
            <ExamStudio
              matrix={matrix}
              questions={questions}
              examMeta={examMeta}
              onGenerateAll={handleGenerateAll}
              isGeneratingAll={isGeneratingAll}
              progress={progress}
              onRegenerateSlot={handleRegenerateSlot}
              onCloneNumbers={handleCloneNumbers}
              onUpdateQuestion={handleUpdateQuestion}
              onOpenExport={handleOpenExport}
              latexCode={latexCode}
              onCompilePdf={handleCompilePdf}
              isCompiling={isCompiling}
            />
          </ViewTransition>
        )}
      </main>

      {/* Modals */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        latexCode={latexCode}
        onCompilePdf={handleCompilePdf}
        isCompiling={isCompiling}
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
