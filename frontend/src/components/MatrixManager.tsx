import React, { useRef } from 'react';
import { 
  Download, Upload, Plus, Trash2, Layers, CheckSquare, 
  AlertCircle, Sparkles, FileSpreadsheet, ArrowRight 
} from 'lucide-react';

export interface ExamSlot {
  slot_id: string;
  slot_number: number;
  part: number;
  type: "MULTIPLE_CHOICE" | "TRUE_FALSE" | "SHORT_ANSWER" | "ESSAY";
  topic: string;
  subtopic?: string;
  level: "NHAN_BIET" | "THONG_HIEU" | "VAN_DUNG" | "VAN_DUNG_CAO";
  points: number;
}

export interface ExamMatrix {
  id: string;
  title: string;
  description?: string;
  subject: string;
  grade: number;
  semester?: string;
  time_minutes: number;
  academic_year: string;
  tags?: string[];
  is_custom?: boolean;
  slots: ExamSlot[];
}

interface MatrixManagerProps {
  matrix: ExamMatrix;
  onUpdateMatrix: (matrix: ExamMatrix) => void;
  onUploadExcel: (file: File) => Promise<void>;
  onDownloadTemplate: () => void;
  onStartGenerate: () => void;
  onOpenCreateMatrix: () => void;
}

export const MatrixManager: React.FC<MatrixManagerProps> = ({
  matrix,
  onUpdateMatrix,
  onUploadExcel,
  onDownloadTemplate,
  onStartGenerate,
  onOpenCreateMatrix
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await onUploadExcel(e.target.files[0]);
    }
  };

  const handleAddSlot = (part: number) => {
    const newNumber = matrix.slots.length + 1;
    const newType = part === 1 ? "MULTIPLE_CHOICE" : part === 2 ? "TRUE_FALSE" : "SHORT_ANSWER";
    const defaultPoints = part === 1 ? 0.25 : part === 2 ? 1.0 : 0.5;

    const newSlot: ExamSlot = {
      slot_id: `slot_${Date.now()}`,
      slot_number: newNumber,
      part: part,
      type: newType,
      topic: "Ứng dụng đạo hàm khảo sát hàm số",
      subtopic: "Tổng quát",
      level: "THONG_HIEU",
      points: defaultPoints
    };
    onUpdateMatrix({
      ...matrix,
      slots: [...matrix.slots, newSlot]
    });
  };

  const handleRemoveSlot = (slotId: string) => {
    onUpdateMatrix({
      ...matrix,
      slots: matrix.slots.filter(s => s.slot_id !== slotId).map((s, idx) => ({ ...s, slot_number: idx + 1 }))
    });
  };

  const levelLabels = {
    NHAN_BIET: { label: "Nhận biết", color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    THONG_HIEU: { label: "Thông hiểu", color: "bg-blue-50 text-blue-700 border-blue-200" },
    VAN_DUNG: { label: "Vận dụng", color: "bg-amber-50 text-amber-700 border-amber-200" },
    VAN_DUNG_CAO: { label: "Vận dụng cao", color: "bg-rose-50 text-rose-700 border-rose-200" }
  };

  const totalPoints = matrix.slots.reduce((sum, s) => sum + (Number(s.points) || 0), 0);
  const isStandard10Points = Math.abs(totalPoints - 10) < 0.01;

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Actions */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-blue-100 text-blue-800 text-xs font-bold rounded-md">
                Lớp {matrix.grade}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {matrix.semester || 'Toàn khóa'} • {matrix.time_minutes} phút
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">
              {matrix.title}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {matrix.description || 'Xem xét kỹ số lượng câu và thang điểm trước khi bắt đầu sinh đề thi.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Tải mẫu Excel */}
            <button
              onClick={onDownloadTemplate}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-2 rounded-lg border border-slate-200 transition-colors duration-150"
              title="Tải file Excel mẫu về máy"
            >
              <Download className="w-4 h-4 text-slate-500" />
              <span>Tải mẫu Excel</span>
            </button>

            {/* Upload Excel */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".xlsx,.xls"
              className="hidden"
              aria-label="Tải lên file Excel ma trận"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-2 rounded-lg border border-blue-200 transition-colors duration-150"
            >
              <Upload className="w-4 h-4 text-blue-600" />
              <span>Tải file Excel lên</span>
            </button>

            {/* Nút Tạo ma trận mới */}
            <button
              onClick={onOpenCreateMatrix}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 transition-colors duration-150"
            >
              <Plus className="w-4 h-4 text-slate-500" />
              <span>Thiết kế mới</span>
            </button>

            {/* Nút Sinh đề theo ma trận này */}
            <button
              onClick={onStartGenerate}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg shadow-sm transition-colors duration-150"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Sinh đề theo ma trận này</span>
            </button>
          </div>
        </div>

        {/* Bảng danh sách các phần */}
        <div className="mt-6 space-y-6">
          {[1, 2, 3].map((partNumber) => {
            const partSlots = matrix.slots.filter(s => s.part === partNumber);
            const partTitles = [
              "",
              "PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (A, B, C, D)",
              "PHẦN II. Câu trắc nghiệm Đúng / Sai (Mỗi câu gồm 4 ý a, b, c, d)",
              "PHẦN III. Câu trắc nghiệm trả lời ngắn (Điền số)"
            ];

            return (
              <div key={partNumber} className="border border-slate-200 rounded-xl overflow-hidden">
                <div className="bg-slate-50 px-4 py-2.5 flex items-center justify-between border-b border-slate-200">
                  <span className="font-bold text-xs md:text-sm text-slate-800">
                    {partTitles[partNumber]} ({partSlots.length} câu)
                  </span>
                  <button
                    onClick={() => handleAddSlot(partNumber)}
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-semibold"
                  >
                    <Plus className="w-3.5 h-3.5" /> Thêm câu
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-100/70 text-slate-600 font-semibold uppercase">
                      <tr>
                        <th className="px-3 py-2 w-12 text-center">STT</th>
                        <th className="px-3 py-2">Chuyên đề / Chủ đề</th>
                        <th className="px-3 py-2">Dạng bài chi tiết</th>
                        <th className="px-3 py-2 w-32">Mức độ</th>
                        <th className="px-3 py-2 w-16 text-center">Điểm</th>
                        <th className="px-3 py-2 w-12 text-center">Xóa</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {partSlots.map((slot) => (
                        <tr key={slot.slot_id} className="hover:bg-slate-50/80 transition-colors duration-150">
                          <td className="px-3 py-2 font-bold text-center text-slate-700">
                            {slot.slot_number}
                          </td>
                          <td className="px-3 py-2 text-slate-900 font-medium">
                            {slot.topic}
                          </td>
                          <td className="px-3 py-2 text-slate-600">
                            {slot.subtopic || '—'}
                          </td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${levelLabels[slot.level]?.color || ''}`}>
                              {levelLabels[slot.level]?.label || slot.level}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-center font-mono font-semibold text-slate-700">
                            {slot.points}
                          </td>
                          <td className="px-3 py-2 text-center">
                            <button
                              onClick={() => handleRemoveSlot(slot.slot_id)}
                              aria-label={`Xóa câu ${slot.slot_number}`}
                              className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors duration-150"
                              title="Xóa slot này"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sticky Bottom Summary Bar (Screen 2 UX requirement) */}
      <div className="sticky bottom-4 z-30 bg-slate-900 text-white rounded-xl shadow-xl p-4 flex flex-wrap items-center justify-between gap-4 border border-slate-800">
        <div className="flex items-center gap-4 text-xs md:text-sm">
          <span>Tổng số câu: <strong className="text-white text-base font-bold">{matrix.slots.length} câu</strong></span>
          <span className="text-slate-500">•</span>
          <span>
            Tổng điểm: <strong className={`text-base font-bold ${isStandard10Points ? 'text-emerald-400' : 'text-amber-400'}`}>
              {totalPoints.toFixed(2)} / 10 điểm
            </strong>
          </span>
          {!isStandard10Points && (
            <span className="hidden md:flex items-center gap-1 text-xs text-amber-300">
              <AlertCircle className="w-3.5 h-3.5" />
              Chưa khớp thang điểm 10 chuẩn
            </span>
          )}
        </div>

        <button
          onClick={onStartGenerate}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs md:text-sm rounded-lg shadow-md transition-colors duration-150"
        >
          <Sparkles className="w-4 h-4 text-amber-300" />
          <span>Bắt đầu Sinh Đề (AI Exam Studio)</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
