import React, { useRef } from 'react';
import { 
  Sparkles, Upload, Layers, Plus, BookOpen, Clock, 
  ArrowRight, FileSpreadsheet, CheckCircle2, ChevronRight, FileText 
} from 'lucide-react';
import { ExamMatrix } from './MatrixManager';

interface DashboardProps {
  onNavigateToGradePicker: () => void;
  onNavigateToMatrixManager: () => void;
  onOpenCreateMatrix: () => void;
  onUploadExcel: (file: File) => Promise<void>;
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

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await onUploadExcel(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Welcome */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 rounded-3xl p-8 md:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>AI Math Exam Generator • Chuẩn Bộ GD&ĐT 2025</span>
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
            Hệ Thống Sinh Đề Thi Toán THPT Bằng AI & LaTeX
          </h1>

          <p className="text-blue-100 text-sm md:text-base leading-relaxed mb-6">
            Bóc tách ma trận đặc tả → AI sinh đề kèm lời giải chi tiết → Ghép khung LaTeX chuẩn 
            <code className="bg-white/20 px-1.5 py-0.5 rounded mx-1 font-mono text-white">ex_test.sty</code> → Xem trước KaTeX & Biên dịch PDF TeX Live.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onNavigateToGradePicker}
              className="inline-flex items-center gap-2 px-5 py-3 bg-white text-blue-700 hover:bg-blue-50 font-bold text-xs md:text-sm rounded-xl shadow-md transition"
            >
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Tạo đề theo Khối Lớp (10, 11, 12)</span>
            </button>

            {currentMatrix && (
              <button
                onClick={onGoToStudio}
                className="inline-flex items-center gap-2 px-5 py-3 bg-white/10 hover:bg-white/20 text-white font-bold text-xs md:text-sm rounded-xl backdrop-blur-md border border-white/20 transition"
              >
                <span>Vào phòng soạn đề hiện tại</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="absolute -right-16 -bottom-16 w-80 h-80 bg-white/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* 3 Quick-Start Cards (Screen 1 UX Wireframe) */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span>Khởi tạo nhanh đề thi</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1: Upload File */}
          <button 
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="bg-white rounded-2xl border-2 border-dashed border-slate-300 hover:border-blue-500 hover:bg-blue-50/30 p-6 flex flex-col justify-between cursor-pointer transition-[border-color,background-color,box-shadow] duration-150 group shadow-xs text-left w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <div>
              <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Upload className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base mb-1 group-hover:text-blue-600 transition-colors">
                1. Tải lên file Ma trận (.xlsx)
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Kéo thả hoặc tải lên bảng đặc tả Excel. Hệ thống sẽ bóc tách tự động thành từng slot câu hỏi.
              </p>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".xlsx,.xls"
              className="hidden"
              aria-label="Tải lên file Excel ma trận đề thi"
            />

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-xs font-semibold text-blue-600 group-hover:translate-x-1 transition-transform">
              <span>Chọn file từ máy tính</span>
              <ChevronRight className="w-4 h-4 ml-1" />
            </div>
          </button>

          {/* Card 2: Mẫu chuẩn Bộ GD&ĐT */}
          <button 
            type="button"
            onClick={onNavigateToGradePicker}
            className="bg-white rounded-2xl border border-slate-200 hover:border-indigo-400 hover:shadow-md p-6 flex flex-col justify-between cursor-pointer transition-[border-color,box-shadow] duration-150 group shadow-xs text-left w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <div>
              <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base mb-1 group-hover:text-indigo-600 transition-colors">
                2. Chọn từ Mẫu chuẩn Bộ GD&ĐT
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Kho ma trận có sẵn theo chuẩn 2025: Đề thi thử THPT Quốc gia 90 phút, Cuối kỳ 1 & 2 Lớp 10, 11, 12.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-xs font-semibold text-indigo-600 group-hover:translate-x-1 transition-transform">
              <span>Khám phá kho mẫu</span>
              <ChevronRight className="w-4 h-4 ml-1" />
            </div>
          </button>

          {/* Card 3: Tự tạo ma trận thủ công */}
          <button 
            type="button"
            onClick={onOpenCreateMatrix}
            className="bg-white rounded-2xl border border-slate-200 hover:border-purple-400 hover:shadow-md p-6 flex flex-col justify-between cursor-pointer transition-[border-color,box-shadow] duration-150 group shadow-xs text-left w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-500"
          >
            <div>
              <div className="w-12 h-12 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Plus className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base mb-1 group-hover:text-purple-600 transition-colors">
                3. Tự thiết kế Ma trận thủ công
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Mở bảng lưới trực quan để tự chọn chủ đề, số câu Phần I, II, III, mức độ nhận thức và điểm số.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-xs font-semibold text-purple-600 group-hover:translate-x-1 transition-transform">
              <span>Bắt đầu thiết kế</span>
              <ChevronRight className="w-4 h-4 ml-1" />
            </div>
          </button>
        </div>
      </div>

      {/* Preset Đề thi Nổi bật */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Bộ đề thi tiêu biểu</h3>
            <p className="text-xs text-slate-500">Bấm để nạp nhanh ma trận và vào thẳng phòng sinh đề</p>
          </div>
          <button
            onClick={onNavigateToGradePicker}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800"
          >
            Xem tất cả →
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              id: "matrix_12_thpt_2025",
              grade: 12,
              title: "Đề Tốt nghiệp THPT 2025 (Chuẩn Bộ GD)",
              desc: "22 câu (12 câu TN 4 lựa chọn, 4 câu Đúng/Sai, 6 câu Trả lời ngắn)",
              time: "90 phút"
            },
            {
              id: "matrix_12_hk1",
              grade: 12,
              title: "Kiểm tra Cuối Học kỳ 1 - Toán 12",
              desc: "Khảo sát hàm số, Vectơ và Hệ trục Oxyz, Thống kê ghép nhóm",
              time: "90 phút"
            },
            {
              id: "matrix_11_hk1",
              grade: 11,
              title: "Kiểm tra Cuối Học kỳ 1 - Toán 11",
              desc: "Lượng giác, Cấp số cộng/nhân, Giới hạn hàm số, Hình không gian song song",
              time: "90 phút"
            }
          ].map(item => (
            <button
              type="button"
              key={item.id}
              onClick={() => onSelectPreset(item.id)}
              className="p-4 rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/30 cursor-pointer transition-[border-color,background-color] duration-150 flex flex-col justify-between text-left w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <div>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-[11px] font-bold rounded">
                  Lớp {item.grade}
                </span>
                <h4 className="font-bold text-slate-900 text-sm mt-2 mb-1">
                  {item.title}
                </h4>
                <p className="text-xs text-slate-500 line-clamp-2">
                  {item.desc}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 w-full">
                <span>{item.time}</span>
                <span className="text-blue-600 font-semibold flex items-center">
                  Dùng mẫu này <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
