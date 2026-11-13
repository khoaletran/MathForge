import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, Clock, Search, ArrowRight, 
  Sparkles, Layers, BookOpen, Filter, Plus, Eye,
  FileSpreadsheet
} from 'lucide-react';
import { ExamMatrix } from './MatrixManager';

interface GradeMatrixPickerProps {
  onSelectMatrix: (matrix: ExamMatrix, autoGenerate?: boolean) => void;
  onOpenCreateMatrix: () => void;
  onUploadExcel: (file: File, grade?: number) => Promise<void>;
}

export const GradeMatrixPicker: React.FC<GradeMatrixPickerProps> = ({
  onSelectMatrix,
  onOpenCreateMatrix,
  onUploadExcel
}) => {
  const [matrices, setMatrices] = useState<ExamMatrix[]>([]);
  const [selectedGrade, setSelectedGrade] = useState<number | 'all'>('all');
  const [selectedSemester, setSelectedSemester] = useState<string>('all');
  const [selectedTopic, setSelectedTopic] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchLibrary();
  }, [selectedGrade, selectedSemester, searchQuery]);

  const fetchLibrary = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedGrade !== 'all') params.append('grade', selectedGrade.toString());
      if (selectedSemester !== 'all') params.append('semester', selectedSemester);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const res = await fetch(`/api/matrix/library?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setMatrices(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const gradeOptions: { id: number | 'all'; label: string }[] = [
    { id: 'all', label: 'Tất cả' },
    { id: 6, label: 'Lớp 6' },
    { id: 7, label: 'Lớp 7' },
    { id: 8, label: 'Lớp 8' },
    { id: 9, label: 'Lớp 9' },
    { id: 10, label: 'Lớp 10' },
    { id: 11, label: 'Lớp 11' },
    { id: 12, label: 'Lớp 12' },
  ];

  const semesterFilters = [
    { id: 'all', label: 'Tất cả đợt' },
    { id: 'Giữa kỳ 1', label: 'Giữa kỳ 1' },
    { id: 'Học kỳ 1', label: 'Cuối kỳ 1' },
    { id: 'Giữa kỳ 2', label: 'Giữa kỳ 2' },
    { id: 'Học kỳ 2', label: 'Cuối kỳ 2' },
    { id: 'Tốt nghiệp THPT', label: 'Tốt nghiệp THPT' },
  ];

  const coreTopics = [
    "Số và Đại số",
    "Hình học và Đo lường",
    "Thống kê và Xác suất",
    "Toán thực tế"
  ];

  const filteredMatrices = matrices.filter(m => {
    if (selectedTopic === 'all') return true;
    return m.slots.some(s => s.topic.toLowerCase().includes(selectedTopic.toLowerCase()));
  });

  return (
    <div className="space-y-5">
      {/* 1. Unified Filter Bar (2 dòng gọn gàng trong 1 khung trắng) */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-4 space-y-3">
        {/* Dòng 1: Segmented Control chọn Khối lớp + Tìm kiếm + Nút Tạo mới */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Segmented Control Lớp */}
          <div className="inline-flex p-1 bg-slate-100 rounded-xl overflow-x-auto text-xs font-semibold shrink-0">
            {gradeOptions.map(tab => (
              <button
                key={String(tab.id)}
                type="button"
                onClick={() => setSelectedGrade(tab.id)}
                className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                  selectedGrade === tab.id
                    ? "bg-white text-blue-700 shadow-xs font-bold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Cụm phải: Search box & Button Tạo mới */}
          <div className="flex items-center gap-2 flex-1 lg:max-w-md justify-end">
            <div className="relative flex-1">
              <Search className="w-4 h-4 stroke-[1.75] text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                aria-label="Tìm theo chương, chủ đề, dạng bài"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm theo chương, chủ đề, dạng bài…"
                className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus:bg-white"
              />
            </div>

            <button
              type="button"
              onClick={onOpenCreateMatrix}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors shrink-0"
            >
              <Plus className="w-4 h-4 stroke-[1.75]" />
              <span className="hidden sm:inline">Thiết kế ma trận mới</span>
              <span className="sm:hidden">Mới</span>
            </button>
          </div>
        </div>

        {/* Dòng 2: Filter Pills cho Mạch kiến thức & Đợt thi */}
        <div className="pt-2.5 border-t border-slate-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
          {/* Mạch kiến thức */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-400 font-semibold inline-flex items-center gap-1 mr-1">
              <Filter className="w-3.5 h-3.5 stroke-[1.75]" />
              <span>Mạch kiến thức:</span>
            </span>
            <button
              type="button"
              onClick={() => setSelectedTopic('all')}
              className={`px-2.5 py-1 rounded-lg transition-colors font-medium ${
                selectedTopic === 'all'
                  ? 'bg-blue-50 text-blue-700 font-bold border border-blue-200'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200/60'
              }`}
            >
              Tất cả 4 chủ đề
            </button>
            {coreTopics.map(top => (
              <button
                key={top}
                type="button"
                onClick={() => setSelectedTopic(top)}
                className={`px-2.5 py-1 rounded-lg transition-colors font-medium ${
                  selectedTopic === top
                    ? 'bg-blue-600 text-white shadow-2xs font-bold'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200/60'
                }`}
              >
                {top}
              </button>
            ))}
          </div>

          {/* Đợt thi */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
            <span className="text-slate-400 font-semibold whitespace-nowrap mr-1">Đợt thi:</span>
            {semesterFilters.map(sem => (
              <button
                key={sem.id}
                type="button"
                onClick={() => setSelectedSemester(sem.id)}
                className={`px-2.5 py-1 rounded-lg whitespace-nowrap transition-colors font-medium ${
                  selectedSemester === sem.id
                    ? 'bg-slate-900 text-white font-bold'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200/60'
                }`}
              >
                {sem.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Grid of Standardized Template Cards */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          Đang tải danh mục ma trận chuẩn...
        </div>
      ) : filteredMatrices.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-xs">
          <BookOpen className="w-10 h-10 stroke-[1.75] text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-800 text-sm">Không tìm thấy ma trận phù hợp</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Vui lòng thử chọn lại khối lớp khác hoặc xóa bớt tiêu chí lọc từ khóa.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMatrices.map(m => {
            const mcCount = m.slots.filter(s => s.type === 'MULTIPLE_CHOICE').length;
            const tfCount = m.slots.filter(s => s.type === 'TRUE_FALSE').length;
            const saCount = m.slots.filter(s => s.type === 'SHORT_ANSWER').length;
            const essayCount = m.slots.filter(s => s.type === 'ESSAY').length;

            return (
              <div
                key={m.id}
                className="bg-white rounded-2xl border border-slate-200/80 hover:border-blue-300 shadow-xs hover:shadow-md transition-all p-5 flex flex-col justify-between group"
              >
                <div>
                  {/* Top row: Badge Lớp + Badge Đợt thi + Thời gian */}
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[11px] font-bold rounded-md border border-blue-200/70">
                        Lớp {m.grade}
                      </span>
                      {m.semester && (
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[11px] font-semibold rounded-md">
                          {m.semester}
                        </span>
                      )}
                    </div>
                    <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 font-medium tabular-nums">
                      <Clock className="w-3.5 h-3.5 stroke-[1.75] text-slate-400" />
                      <span>{m.time_minutes} phút</span>
                    </span>
                  </div>

                  {/* Title & Description */}
                  <h3 className="font-bold text-slate-900 text-sm mb-1.5 line-clamp-1 group-hover:text-blue-600 transition-colors">
                    {m.title}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4 line-clamp-2">
                    {m.description || `Đặc tả kiểm tra chuẩn môn Toán Lớp ${m.grade} theo chương trình GDPT 2018.`}
                  </p>

                  {/* Metadata Box: Hàng Stat Badges ngang gọn đẹp */}
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 mb-4 flex items-center justify-between text-xs tabular-nums">
                    <span className="font-bold text-slate-800">
                      Tổng: {m.slots.length} câu
                    </span>
                    <div className="flex items-center gap-2 text-[11px] text-slate-600 font-medium">
                      {mcCount > 0 && <span>TN: <strong className="text-blue-600">{mcCount}</strong></span>}
                      {tfCount > 0 && <span>Đ/S: <strong className="text-emerald-600">{tfCount}</strong></span>}
                      {saCount > 0 && <span>TLN: <strong className="text-amber-600">{saCount}</strong></span>}
                      {essayCount > 0 && <span>TL: <strong className="text-violet-600">{essayCount}</strong></span>}
                    </div>
                  </div>
                </div>

                {/* Actions Footer: Nút phụ 50% + Nút chính 50% */}
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => onSelectMatrix(m, false)}
                    className="inline-flex items-center justify-center gap-1.5 py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5 stroke-[1.75]" />
                    <span>Xem ma trận</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => onSelectMatrix(m, true)}
                    className="inline-flex items-center justify-center gap-1.5 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 stroke-[1.75]" />
                    <span>Sinh đề ngay</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
