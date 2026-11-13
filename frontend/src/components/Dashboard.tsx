import React, { useRef, useState } from 'react';
import { 
  Sparkles, Upload, Layers, Plus, Clock, 
  ArrowRight, ArrowUpRight, FileSpreadsheet, ChevronRight,
  FileCheck2, SlidersHorizontal, BookOpen, CheckCircle2
} from 'lucide-react';
import { ExamMatrix } from './MatrixManager';

interface DashboardProps {
  onNavigateToGradePicker: () => void;
  onNavigateToMatrixManager: () => void;
  onOpenCreateMatrix: () => void;
  onUploadExcel: (file: File, grade?: number) => Promise<void>;
  onSelectPreset: (matrixId: string) => Promise<void>;
  currentMatrix: ExamMatrix | null;
  onGoToStudio: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  onNavigateToGradePicker,
  onNavigateToMatrixManager,
  onOpenCreateMatrix,
  onUploadExcel,
  onSelectPreset,
  currentMatrix,
  onGoToStudio
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadGrade, setUploadGrade] = useState<number>(12);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedStructure, setSelectedStructure] = useState<'3part' | 'mc_essay'>('3part');

  const gradePills = [
    { label: 'THCS', value: 9 },
    { label: '10', value: 10 },
    { label: '11', value: 11 },
    { label: '12', value: 12 },
  ];

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await onUploadExcel(e.target.files[0], uploadGrade);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        await onUploadExcel(file, uploadGrade);
      }
    }
  };

  const featuredExams = [
    {
      id: "matrix_12_thpt_2025",
      grade: 12,
      term: "Tốt nghiệp THPT 2026",
      title: "Đề Tốt nghiệp THPT Quốc Gia (Chuẩn Bộ GD&ĐT)",
      time: "90 phút",
      totalQuestions: 22,
      parts: [
        { label: "TN", count: 12, color: "bg-blue-600", width: "54.5%" },
        { label: "Đ/S", count: 4, color: "bg-emerald-500", width: "18.2%" },
        { label: "TLN", count: 6, color: "bg-amber-500", width: "27.3%" },
      ]
    },
    {
      id: "matrix_12_ck1",
      grade: 12,
      term: "Học kỳ 1",
      title: "Kiểm tra Cuối Học kỳ 1 - Toán 12",
      time: "90 phút",
      totalQuestions: 22,
      parts: [
        { label: "TN", count: 12, color: "bg-blue-600", width: "54.5%" },
        { label: "Đ/S", count: 4, color: "bg-emerald-500", width: "18.2%" },
        { label: "TLN", count: 6, color: "bg-amber-500", width: "27.3%" },
      ]
    },
    {
      id: "matrix_9_gk1",
      grade: 9,
      term: "Giữa kỳ 1",
      title: "Kiểm tra Giữa Học kỳ 1 - Toán 9 (Thi vào 10)",
      time: "90 phút",
      totalQuestions: 19,
      parts: [
        { label: "TN", count: 12, color: "bg-blue-600", width: "63.2%" },
        { label: "Tự luận", count: 7, color: "bg-violet-500", width: "36.8%" },
      ]
    }
  ];

  return (
    <div className="space-y-6">
      {/* 1. Compact Header Bar (1 dòng duy nhất) */}
      <div className="bg-white border border-slate-200/80 rounded-2xl px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Không gian soạn đề Toán
          </h1>
          <p className="text-sm text-slate-500 font-medium">
            Chuẩn cấu trúc GDPT 2018 & gói lệnh LaTeX <code className="font-mono text-xs font-semibold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">ex_test.sty</code>
          </p>
        </div>

        {currentMatrix && (
          <button
            onClick={onGoToStudio}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs md:text-sm font-semibold rounded-xl border border-blue-200 transition-colors shrink-0"
          >
            <span>Vào phòng soạn đề hiện tại</span>
            <ArrowUpRight className="w-4 h-4 stroke-[1.75] shrink-0" />
          </button>
        )}
      </div>

      {/* 2. Khu vực Khởi tạo nhanh đề thi (3 Bento Action Cards) */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-600">
            Khởi tạo nhanh đề thi
          </h2>
          <span className="text-xs text-slate-400 font-medium">
            Chọn 1 trong 3 phương thức bắt đầu
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Card 1: Tải lên file Ma trận (.xlsx) */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 flex flex-col justify-between hover:border-slate-300 transition-colors">
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <FileSpreadsheet className="w-5 h-5 stroke-[1.75]" />
                </div>

                {/* Segmented Pills chọn khối lớp */}
                <div className="inline-flex p-0.5 bg-slate-100 rounded-lg text-xs font-semibold">
                  {gradePills.map((pill) => (
                    <button
                      key={pill.label}
                      type="button"
                      onClick={() => setUploadGrade(pill.value)}
                      className={`px-2 py-0.5 rounded-md transition-all ${
                        uploadGrade === pill.value
                          ? 'bg-white text-blue-700 shadow-xs font-bold'
                          : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {pill.label}
                    </button>
                  ))}
                </div>
              </div>

              <h3 className="font-bold text-slate-900 text-sm mb-1">
                Tải lên file Ma trận (.xlsx)
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-3">
                Kéo thả file bảng đặc tả Excel hoặc chọn từ máy tính để AI số hóa thành các slot câu hỏi.
              </p>

              {/* Vùng Drag & Drop trực tiếp */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
                  isDragging 
                    ? 'border-blue-500 bg-blue-50/60' 
                    : 'border-slate-200 hover:border-blue-400 hover:bg-blue-50/30'
                }`}
              >
                <Upload className="w-5 h-5 stroke-[1.75] text-slate-400 mx-auto mb-1.5" />
                <span className="text-xs font-semibold text-slate-700 block">
                  Kéo thả file .xlsx vào đây
                </span>
                <span className="text-[11px] text-slate-400">
                  hoặc bấm để duyệt file
                </span>
              </div>

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".xlsx,.xls"
                className="hidden"
                aria-label="Tải lên file Excel ma trận đề thi"
              />
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>Đang chọn: <strong>Lớp {uploadGrade}</strong></span>
              <span className="text-blue-600 font-semibold flex items-center gap-1">
                Tải lên <ChevronRight className="w-3.5 h-3.5 stroke-[1.75]" />
              </span>
            </div>
          </div>

          {/* Card 2: Chọn từ Mẫu chuẩn Bộ GD&ĐT */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 flex flex-col justify-between hover:border-slate-300 transition-colors">
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Layers className="w-5 h-5 stroke-[1.75]" />
                </div>
                <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-100">
                  29 Ma trận chuẩn
                </span>
              </div>

              <h3 className="font-bold text-slate-900 text-sm mb-1">
                Chọn từ Mẫu chuẩn Bộ GD&ĐT
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-3">
                Kho mẫu chuẩn hóa GDPT 2018 Lớp 6–12, nạp nhanh chỉ với 1 click:
              </p>

              {/* 3 Quick Chips */}
              <div className="space-y-1.5">
                {[
                  { id: "matrix_12_thpt_2025", title: "THPT Quốc Gia 2026 (90p)", badge: "Lớp 12" },
                  { id: "matrix_12_ck1", title: "Cuối kỳ 1 - Toán 12", badge: "Lớp 12" },
                  { id: "matrix_9_gk1", title: "Giữa kỳ 1 - Toán 9", badge: "Lớp 9" },
                ].map((chip) => (
                  <button
                    key={chip.id}
                    type="button"
                    onClick={() => onSelectPreset(chip.id)}
                    className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-indigo-50/70 border border-slate-200/60 hover:border-indigo-200 text-left transition-colors group"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileCheck2 className="w-4 h-4 stroke-[1.75] text-indigo-600 shrink-0" />
                      <span className="text-xs font-medium text-slate-800 truncate group-hover:text-indigo-900">
                        {chip.title}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
                      {chip.badge}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={onNavigateToGradePicker}
                className="w-full flex items-center justify-between text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
              >
                <span>Khám phá toàn bộ kho mẫu</span>
                <ChevronRight className="w-4 h-4 stroke-[1.75]" />
              </button>
            </div>
          </div>

          {/* Card 3: Tự thiết kế Ma trận từ đầu */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 flex flex-col justify-between hover:border-slate-300 transition-colors">
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="w-10 h-10 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                  <SlidersHorizontal className="w-5 h-5 stroke-[1.75]" />
                </div>
                <span className="text-xs font-semibold text-violet-700 bg-violet-50 px-2 py-0.5 rounded-full border border-violet-100">
                  Tùy biến 100%
                </span>
              </div>

              <h3 className="font-bold text-slate-900 text-sm mb-1">
                Tự thiết kế Ma trận từ đầu
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-3">
                Chọn trước cấu trúc khung đề để khởi tạo nhanh ma trận theo ý bạn:
              </p>

              {/* Lựa chọn cấu trúc khung đề */}
              <div className="space-y-2">
                <label 
                  onClick={() => setSelectedStructure('3part')}
                  className={`flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition-colors ${
                    selectedStructure === '3part'
                      ? 'bg-violet-50/70 border-violet-300 text-violet-950 font-medium'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <input
                    type="radio"
                    name="structure"
                    checked={selectedStructure === '3part'}
                    onChange={() => setSelectedStructure('3part')}
                    className="mt-0.5 text-violet-600 focus:ring-violet-500"
                  />
                  <div>
                    <span className="font-bold block">Chuẩn 3 phần mới</span>
                    <span className="text-[11px] text-slate-500">Trắc nghiệm + Đúng/Sai + Trả lời ngắn</span>
                  </div>
                </label>

                <label 
                  onClick={() => setSelectedStructure('mc_essay')}
                  className={`flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition-colors ${
                    selectedStructure === 'mc_essay'
                      ? 'bg-violet-50/70 border-violet-300 text-violet-950 font-medium'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <input
                    type="radio"
                    name="structure"
                    checked={selectedStructure === 'mc_essay'}
                    onChange={() => setSelectedStructure('mc_essay')}
                    className="mt-0.5 text-violet-600 focus:ring-violet-500"
                  />
                  <div>
                    <span className="font-bold block">Kết hợp truyền thống</span>
                    <span className="text-[11px] text-slate-500">Trắc nghiệm 4 lựa chọn + Tự luận</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={onOpenCreateMatrix}
                className="w-full inline-flex items-center justify-center gap-1.5 py-2 bg-violet-600 hover:bg-violet-700 text-white text-xs font-bold rounded-lg shadow-xs transition-colors"
              >
                <Plus className="w-4 h-4 stroke-[1.75]" />
                <span>Mở trình thiết kế ma trận</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Khu vực "Bộ đề tiêu biểu & Đề gần đây" với Segmented Bar trực quan */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
          <div>
            <h3 className="font-bold text-slate-900 text-base">
              Bộ đề tiêu biểu & Đề mẫu
            </h3>
            <p className="text-xs text-slate-500">
              Chọn mẫu ma trận để nạp và tiến hành sinh đề thi tự động
            </p>
          </div>
          <button
            onClick={onNavigateToGradePicker}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <span>Xem tất cả 29 ma trận</span>
            <ChevronRight className="w-3.5 h-3.5 stroke-[1.75]" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {featuredExams.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-xl border border-slate-200/80 hover:border-blue-400 bg-white hover:bg-slate-50/40 transition-all flex flex-col justify-between group shadow-2xs"
            >
              <div>
                {/* Header: Badge Lớp + Thời gian */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[11px] font-bold rounded-md border border-blue-200/70">
                      Lớp {item.grade}
                    </span>
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] font-semibold rounded-md">
                      {item.term}
                    </span>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 font-medium tabular-nums">
                    <Clock className="w-3.5 h-3.5 stroke-[1.75] text-slate-400" />
                    <span>{item.time}</span>
                  </span>
                </div>

                {/* Tiêu đề đề thi */}
                <h4 className="font-bold text-slate-900 text-sm mb-3 line-clamp-1 group-hover:text-blue-600 transition-colors">
                  {item.title}
                </h4>

                {/* Thanh phân bổ cấu trúc trực quan (Segmented Bar) */}
                <div className="space-y-1.5 mb-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-medium">Cấu trúc phân bổ ({item.totalQuestions} câu):</span>
                  </div>
                  <div className="w-full h-2 rounded-full overflow-hidden bg-slate-100 flex">
                    {item.parts.map((p, idx) => (
                      <div
                        key={idx}
                        className={`${p.color} h-full transition-all`}
                        style={{ width: p.width }}
                        title={`${p.label}: ${p.count} câu`}
                      />
                    ))}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-slate-500">
                    {item.parts.map((p, idx) => (
                      <div key={idx} className="flex items-center gap-1">
                        <span className={`w-2 h-2 rounded-full ${p.color}`} />
                        <span>{p.label}: <strong className="text-slate-700 tabular-nums">{p.count}</strong></span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-400 tabular-nums">
                  Tổng: {item.totalQuestions} câu • 10đ
                </span>
                <button
                  type="button"
                  onClick={() => onSelectPreset(item.id)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-2xs transition-colors"
                >
                  <span>Dùng mẫu</span>
                  <ArrowRight className="w-3.5 h-3.5 stroke-[1.75]" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
