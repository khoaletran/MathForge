import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, Calendar, Clock, CheckCircle, Search, ArrowRight, 
  Sparkles, Layers, BookOpen, Filter, Plus, FileText, ChevronRight 
} from 'lucide-react';
import { ExamMatrix } from './MatrixManager';

interface GradeMatrixPickerProps {
  onSelectMatrix: (matrix: ExamMatrix, autoGenerate?: boolean) => void;
  onOpenCreateMatrix: () => void;
  onUploadExcel: (file: File) => Promise<void>;
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

  const gradeTabs = [
    { id: 'all', label: 'Tất cả khối lớp' },
    // Cấp THCS (Lớp 6 - 9)
    { id: 6, label: 'Lớp 6' },
    { id: 7, label: 'Lớp 7' },
    { id: 8, label: 'Lớp 8' },
    { id: 9, label: 'Lớp 9 (Thi vào 10)' },
    // Cấp THPT (Lớp 10 - 12)
    { id: 10, label: 'Lớp 10' },
    { id: 11, label: 'Lớp 11' },
    { id: 12, label: 'Lớp 12 (Tốt nghiệp)' },
  ];

  const semesterFilters = [
    { id: 'all', label: 'Tất cả học kỳ' },
    { id: 'Giữa kỳ 1', label: 'Giữa kỳ 1' },
    { id: 'Học kỳ 1', label: 'Cuối kỳ 1' },
    { id: 'Giữa kỳ 2', label: 'Giữa kỳ 2' },
    { id: 'Học kỳ 2', label: 'Cuối kỳ 2' },
    { id: 'Thi vào 10', label: 'Thi vào 10 (2026)' },
    { id: 'Tốt nghiệp THPT', label: 'Tốt nghiệp THPT (2026)' },
  ];

  const coreTopics = [
    "Số và Đại số",
    "Hình học và Đo lường",
    "Thống kê và Xác suất",
    "Toán thực tế"
  ];

  const filteredMatrices = matrices.filter(m => {
    if (selectedTopic === 'all') return true;
    const hasTopic = m.slots.some(s => s.topic.toLowerCase().includes(selectedTopic.toLowerCase()));
    return hasTopic;
  });

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 rounded-2xl p-6 md:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Kho Ma Trận Chuẩn Hóa Lớp 6 - 12 (Bộ GD&ĐT 2026)</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-2">
            Chọn Ma Trận Đề Thi Môn Toán (Lớp 6 đến Lớp 12)
          </h2>
          <p className="text-blue-100 text-sm md:text-base leading-relaxed">
            Đầy đủ 4 chủ đề cốt lõi theo chương trình GDPT 2018 mới nhất: 
            <strong> Số và Đại số</strong>, <strong>Hình học và Đo lường</strong>, <strong>Thống kê và Xác suất</strong>, và <strong>Toán thực tế</strong>.
            Tương thích trọn vẹn với các bộ sách Kết nối tri thức, Cánh Diều, Chân trời sáng tạo.
          </p>
        </div>

        <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-white/10 rounded-full blur-2xl pointer-events-none" />
      </div>

      {/* Grade Selector Tabs & Filters */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-4">
        {/* Khối lớp selector */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex flex-wrap items-center gap-1.5">
            {gradeTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedGrade(tab.id as any)}
                className={`px-3.5 py-1.5 rounded-lg text-xs md:text-sm font-bold transition-[background-color,color,box-shadow] duration-150 ${
                  selectedGrade === tab.id
                    ? "bg-blue-600 text-white shadow-xs"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            onClick={onOpenCreateMatrix}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold rounded-lg border border-indigo-200 transition-colors duration-150"
          >
            <Plus className="w-4 h-4" />
            <span>Thiết kế ma trận mới</span>
          </button>
        </div>

        {/* 4 Mạch kiến thức tags & Học kỳ filter */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pt-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-slate-500 font-semibold mr-1">4 Chủ đề:</span>
            <button
              onClick={() => setSelectedTopic('all')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-colors duration-150 ${
                selectedTopic === 'all'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              Tất cả 4 chủ đề
            </button>
            {coreTopics.map(top => (
              <button
                key={top}
                onClick={() => setSelectedTopic(top)}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-colors duration-150 ${
                  selectedTopic === top
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {top}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              aria-label="Tìm kiếm ma trận theo chủ đề, dạng bài"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm theo chủ đề, dạng bài…"
              className="w-full text-xs pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            />
          </div>
        </div>

        {/* Semester filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-500 font-semibold mr-1 whitespace-nowrap">Đợt thi:</span>
          {semesterFilters.map(sem => (
            <button
              key={sem.id}
              onClick={() => setSelectedSemester(sem.id)}
              className={`px-3 py-1 rounded-md whitespace-nowrap transition ${
                selectedSemester === sem.id
                  ? "bg-slate-800 text-white font-bold"
                  : "bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200"
              }`}
            >
              {sem.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Matrices */}
      {loading ? (
        <div className="py-12 text-center text-slate-400 text-sm">
          Đang tải danh sách ma trận...
        </div>
      ) : filteredMatrices.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-700 text-base">Không tìm thấy ma trận phù hợp</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Thử chuyển sang "Tất cả khối lớp" hoặc xóa từ khóa tìm kiếm.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredMatrices.map(m => {
            const p1 = m.slots.filter(s => s.part === 1).length;
            const p2 = m.slots.filter(s => s.part === 2).length;
            const p3 = m.slots.filter(s => s.part === 3).length;

            return (
              <div
                key={m.id}
                className="bg-white rounded-xl border border-slate-200 hover:border-blue-400 shadow-sm hover:shadow-md transition-[border-color,box-shadow] duration-150 p-5 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 text-xs font-bold rounded-md border border-blue-200">
                      Lớp {m.grade}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">
                      {m.semester || 'Toàn khóa'}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-base group-hover:text-blue-600 transition-colors line-clamp-2 mb-2">
                    {m.title}
                  </h3>

                  <p className="text-xs text-slate-500 line-clamp-2 mb-4 leading-relaxed">
                    {m.description || 'Ma trận chuẩn GDPT 2018 theo định dạng Bộ GD&ĐT 2026.'}
                  </p>

                  {/* 4 Chủ đề tags hiển thị */}
                  <div className="flex flex-wrap gap-1 mb-3">
                    {Array.from(new Set(m.slots.map(s => s.topic))).slice(0, 3).map(top => (
                      <span key={top} className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                        {top}
                      </span>
                    ))}
                  </div>

                  {/* Cấu trúc câu hỏi */}
                  <div className="bg-slate-50 rounded-lg p-3 space-y-1.5 text-xs text-slate-600 mb-4 border border-slate-100">
                    <div className="flex items-center justify-between">
                      <span>Tổng số câu:</span>
                      <strong className="text-slate-900">{m.slots.length} câu</strong>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>• Phần I (4 lựa chọn):</span>
                      <span>{p1} câu</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>• Phần II (Đúng/Sai):</span>
                      <span>{p2} câu</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>• Phần III (Trả lời ngắn):</span>
                      <span>{p3} câu</span>
                    </div>
                    <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                      <span>Thời gian:</span>
                      <span className="font-semibold text-slate-800">{m.time_minutes} phút</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => onSelectMatrix(m, false)}
                    className="flex-1 py-2 px-3 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                  >
                    Xem ma trận
                  </button>

                  <button
                    onClick={() => onSelectMatrix(m, true)}
                    className="flex-1 inline-flex items-center justify-center gap-1 py-2 px-3 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
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
