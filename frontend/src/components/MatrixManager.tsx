import React, { useRef } from 'react';
import { 
  Download, Upload, Plus, Trash2, Layers, CheckSquare, 
  AlertCircle, AlertTriangle, Sparkles, FileSpreadsheet, ArrowRight, FileText, CheckCircle2,
  CopyPlus, SlidersHorizontal, TableProperties
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
  onUploadExcel: (file: File, grade?: number) => Promise<void>;
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
      await onUploadExcel(e.target.files[0], matrix.grade);
    }
  };

  // Thêm slot mới vào một phần chỉ định
  const handleAddSlot = (partNumber: number, forcedType?: ExamSlot["type"]) => {
    const partSlots = matrix.slots.filter(s => s.part === partNumber);
    const targetType = forcedType || (partSlots.length > 0 ? partSlots[partSlots.length - 1].type : (partNumber === 1 ? "MULTIPLE_CHOICE" : partNumber === 2 ? "TRUE_FALSE" : "SHORT_ANSWER"));
    
    let defaultPoints = 0.25;
    if (targetType === "TRUE_FALSE") defaultPoints = 1.0;
    else if (targetType === "SHORT_ANSWER") defaultPoints = 0.5;
    else if (targetType === "ESSAY") defaultPoints = 1.0;

    const newSlot: ExamSlot = {
      slot_id: `slot_${Date.now()}_${matrix.slots.length + 1}`,
      slot_number: matrix.slots.length + 1,
      part: partNumber,
      type: targetType,
      topic: "Số và Đại số",
      subtopic: "Tổng quát",
      level: "THONG_HIEU",
      points: defaultPoints
    };

    const newSlots = [...matrix.slots, newSlot].map((s, idx) => ({ ...s, slot_number: idx + 1 }));
    onUpdateMatrix({
      ...matrix,
      slots: newSlots
    });
  };

  // Nhân bản một slot câu hỏi ngay bên dưới
  const handleCloneSlot = (slotToClone: ExamSlot) => {
    const clone: ExamSlot = {
      ...slotToClone,
      slot_id: `slot_${Date.now()}_${matrix.slots.length + 1}`,
      slot_number: slotToClone.slot_number + 1,
    };

    // Chèn clone ngay sau slot gốc
    const targetIndex = matrix.slots.findIndex(s => s.slot_id === slotToClone.slot_id);
    const updated = [...matrix.slots];
    if (targetIndex >= 0) {
      updated.splice(targetIndex + 1, 0, clone);
    } else {
      updated.push(clone);
    }

    onUpdateMatrix({
      ...matrix,
      slots: updated.map((s, idx) => ({ ...s, slot_number: idx + 1 }))
    });
  };

  // Thêm một phần thi mới (Part max + 1)
  const handleAddNewPart = (type: ExamSlot["type"]) => {
    const maxPart = matrix.slots.length > 0 ? Math.max(...matrix.slots.map(s => s.part)) : 0;
    const nextPart = maxPart + 1;
    handleAddSlot(nextPart, type);
  };

  const handleRemoveSlot = (slotId: string) => {
    const remaining = matrix.slots.filter(s => s.slot_id !== slotId);
    onUpdateMatrix({
      ...matrix,
      slots: remaining.map((s, idx) => ({ ...s, slot_number: idx + 1 }))
    });
  };

  const handleSlotChange = (slotId: string, field: keyof ExamSlot, val: any) => {
    const updated = matrix.slots.map(s => {
      if (s.slot_id === slotId) {
        return { ...s, [field]: val };
      }
      return s;
    });
    onUpdateMatrix({ ...matrix, slots: updated });
  };

  // Nhóm các slots theo Phần thi
  const partsToRender = Array.from(new Set(matrix.slots.map(s => s.part))).sort((a, b) => a - b);
  if (partsToRender.length === 0) partsToRender.push(1);

  const getPartTitle = (partNum: number, slotsInPart: ExamSlot[]) => {
    const sample = slotsInPart[0];
    if (!sample) return `PHẦN ${partNum}`;
    if (sample.type === 'MULTIPLE_CHOICE') return `PHẦN ${partNum}. CÂU TRẮC NGHIỆM 4 LỰA CHỌN`;
    if (sample.type === 'TRUE_FALSE') return `PHẦN ${partNum}. CÂU TRẮC NGHIỆM ĐÚNG / SAI`;
    if (sample.type === 'SHORT_ANSWER') return `PHẦN ${partNum}. CÂU HỎI TRẢ LỜI NGẮN (ĐIỀN SỐ)`;
    if (sample.type === 'ESSAY') return `PHẦN ${partNum}. CÂU HỎI TỰ LUẬN BÀI TẬP`;
    return `PHẦN ${partNum}`;
  };

  // Tính toán tổng điểm và tỷ lệ mức độ nhận thức
  const totalPoints = matrix.slots.reduce((sum, s) => sum + (Number(s.points) || 0), 0);
  const totalSlotsCount = matrix.slots.length;
  const isPointsBalanced = Math.abs(totalPoints - 10.0) < 0.05;

  const countNB = matrix.slots.filter(s => s.level === 'NHAN_BIET').length;
  const countTH = matrix.slots.filter(s => s.level === 'THONG_HIEU').length;
  const countVD = matrix.slots.filter(s => s.level === 'VAN_DUNG').length;
  const countVDC = matrix.slots.filter(s => s.level === 'VAN_DUNG_CAO').length;

  const pctNB = totalSlotsCount > 0 ? Math.round((countNB / totalSlotsCount) * 100) : 0;
  const pctTH = totalSlotsCount > 0 ? Math.round((countTH / totalSlotsCount) * 100) : 0;
  const pctVD = totalSlotsCount > 0 ? Math.round((countVD / totalSlotsCount) * 100) : 0;
  const pctVDC = totalSlotsCount > 0 ? Math.round((countVDC / totalSlotsCount) * 100) : 0;

  return (
    <div className="space-y-6 pb-24">
      {/* 1. Header Card Thông Tin Ma Trận */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 font-bold text-xs rounded-md border border-blue-200/70">
                Lớp {matrix.grade}
              </span>
              {matrix.semester && (
                <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-xs font-semibold rounded-md">
                  {matrix.semester}
                </span>
              )}
              <span className="text-xs text-slate-500 font-medium tabular-nums">
                • Thời gian: <strong>{matrix.time_minutes} phút</strong>
              </span>
            </div>
            <h1 className="text-lg md:text-xl font-bold text-slate-900 tracking-tight">
              {matrix.title}
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              {matrix.description || "Bảng đặc tả cấu trúc đề thi theo chuẩn Bộ Giáo Dục & Đào Tạo."}
            </p>
          </div>

          {/* Quick Excel Action Buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={onDownloadTemplate}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
              title="Tải bảng đặc tả này về máy tính định dạng Excel .xlsx"
            >
              <Download className="w-4 h-4 stroke-[1.75]" />
              <span>Tải mẫu Excel</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
              title="Nhập bảng đặc tả từ file Excel .xlsx"
            >
              <Upload className="w-4 h-4 stroke-[1.75]" />
              <span>Nhập Excel</span>
            </button>

            <button
              type="button"
              onClick={onOpenCreateMatrix}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4 stroke-[1.75]" />
              <span>Tạo mới</span>
            </button>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".xlsx,.xls"
              className="hidden"
              aria-label="Tải lên file Excel ma trận"
            />
          </div>
        </div>

        {/* Thanh thêm nhanh các dạng câu */}
        <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-slate-600">Thêm nhanh câu:</span>
            <button
              type="button"
              onClick={() => handleAddNewPart("MULTIPLE_CHOICE")}
              className="px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg border border-blue-200 font-medium transition-colors"
            >
              + Trắc nghiệm (0.25đ)
            </button>
            <button
              type="button"
              onClick={() => handleAddNewPart("TRUE_FALSE")}
              className="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg border border-emerald-200 font-medium transition-colors"
            >
              + Đúng / Sai (1.0đ)
            </button>
            <button
              type="button"
              onClick={() => handleAddNewPart("SHORT_ANSWER")}
              className="px-2.5 py-1 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded-lg border border-amber-200 font-medium transition-colors"
            >
              + Trả lời ngắn (0.5đ)
            </button>
            <button
              type="button"
              onClick={() => handleAddNewPart("ESSAY")}
              className="px-2.5 py-1 bg-violet-50 text-violet-700 hover:bg-violet-100 rounded-lg border border-violet-200 font-medium transition-colors"
            >
              + Tự luận (1.0đ)
            </button>
          </div>
          <span className="text-slate-400 text-[11px] font-medium hidden md:inline">
            Tự động đồng bộ với cấu trúc gói lệnh LaTeX ex_test.sty
          </span>
        </div>
      </div>

      {/* 2. Danh Sách Các Phần (Bảng Ma Trận Tối Ưu UX) */}
      <div className="space-y-5">
        {partsToRender.map((partNumber) => {
          const partSlots = matrix.slots.filter(s => s.part === partNumber);
          const partPoints = partSlots.reduce((sum, s) => sum + (Number(s.points) || 0), 0);

          return (
            <div key={partNumber} className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
              {/* Header của từng Phần */}
              <div className="bg-slate-50/80 px-5 py-3 flex items-center justify-between border-b border-slate-200/80">
                <div className="flex items-center gap-2.5">
                  <span className="font-bold text-xs md:text-sm text-slate-900 tracking-tight">
                    {getPartTitle(partNumber, partSlots)}
                  </span>
                  <span className="px-2 py-0.5 bg-slate-200/80 text-slate-700 rounded-md text-xs font-semibold tabular-nums">
                    {partSlots.length} câu • {partPoints.toFixed(2)}đ
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => handleAddSlot(partNumber)}
                  className="inline-flex items-center gap-1 text-xs text-blue-700 hover:text-blue-900 font-semibold px-2.5 py-1 bg-blue-50 hover:bg-blue-100 border border-blue-200/60 rounded-lg transition-colors"
                >
                  <Plus className="w-3.5 h-3.5 stroke-[1.75]" />
                  <span>Thêm câu vào phần này</span>
                </button>
              </div>

              {/* Bảng Slots đã loại bỏ cột DẠNG THỨC bị lặp */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200/60">
                    <tr>
                      <th className="px-3.5 py-2.5 w-12 text-center">STT</th>
                      <th className="px-3.5 py-2.5 w-[28%]">Chuyên đề / Mạch nội dung</th>
                      <th className="px-3.5 py-2.5 w-[42%]">Dạng bài chi tiết</th>
                      <th className="px-3.5 py-2.5 w-44">Mức độ nhận thức</th>
                      <th className="px-3.5 py-2.5 w-20 text-center">Điểm</th>
                      <th className="px-3.5 py-2.5 w-20 text-center">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {partSlots.map((slot) => (
                      <tr key={slot.slot_id} className="hover:bg-slate-50/60 transition-colors">
                        {/* STT */}
                        <td className="px-3.5 py-2.5 font-bold text-center text-slate-700 tabular-nums">
                          {slot.slot_number}
                        </td>

                        {/* Chuyên đề / Mạch nội dung */}
                        <td className="px-3.5 py-2.5 text-slate-900 font-medium">
                          <input
                            type="text"
                            value={slot.topic}
                            onChange={(e) => handleSlotChange(slot.slot_id, 'topic', e.target.value)}
                            className="w-full px-2 py-1 border border-transparent hover:border-slate-300 focus:border-blue-500 rounded-lg text-xs bg-transparent focus:bg-white focus:outline-none transition-colors"
                          />
                        </td>

                        {/* Dạng bài chi tiết */}
                        <td className="px-3.5 py-2.5 text-slate-700">
                          <input
                            type="text"
                            value={slot.subtopic || ''}
                            placeholder="Dạng bài chi tiết..."
                            onChange={(e) => handleSlotChange(slot.slot_id, 'subtopic', e.target.value)}
                            className="w-full px-2 py-1 border border-transparent hover:border-slate-300 focus:border-blue-500 rounded-lg text-xs bg-transparent focus:bg-white focus:outline-none transition-colors"
                          />
                        </td>

                        {/* Mức độ: Inline Segmented Pills 1 chạm */}
                        <td className="px-3.5 py-2.5">
                          <div className="inline-flex p-0.5 bg-slate-100 rounded-lg gap-0.5">
                            {[
                              { id: 'NHAN_BIET', label: 'NB', activeClass: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold shadow-2xs' },
                              { id: 'THONG_HIEU', label: 'TH', activeClass: 'bg-blue-50 text-blue-800 border-blue-300 font-bold shadow-2xs' },
                              { id: 'VAN_DUNG', label: 'VD', activeClass: 'bg-amber-50 text-amber-800 border-amber-300 font-bold shadow-2xs' },
                              { id: 'VAN_DUNG_CAO', label: 'VDC', activeClass: 'bg-rose-50 text-rose-800 border-rose-300 font-bold shadow-2xs' },
                            ].map((pill) => (
                              <button
                                key={pill.id}
                                type="button"
                                onClick={() => handleSlotChange(slot.slot_id, 'level', pill.id)}
                                className={`px-2 py-0.5 rounded text-[11px] font-semibold border transition-all ${
                                  slot.level === pill.id
                                    ? pill.activeClass
                                    : 'border-transparent text-slate-500 hover:text-slate-800'
                                }`}
                                title={pill.id === 'NHAN_BIET' ? 'Nhận biết' : pill.id === 'THONG_HIEU' ? 'Thông hiểu' : pill.id === 'VAN_DUNG' ? 'Vận dụng' : 'Vận dụng cao'}
                              >
                                {pill.label}
                              </button>
                            ))}
                          </div>
                        </td>

                        {/* Điểm số */}
                        <td className="px-3.5 py-2.5 text-center">
                          <input
                            type="number"
                            step="0.05"
                            min="0.05"
                            max="10"
                            value={slot.points}
                            onChange={(e) => handleSlotChange(slot.slot_id, 'points', parseFloat(e.target.value) || 0)}
                            className="w-16 px-1.5 py-1 border border-slate-200 rounded-lg text-center font-mono font-semibold text-xs tabular-nums focus:outline-none focus:border-blue-500 bg-white"
                          />
                        </td>

                        {/* Row Quick Actions: CopyPlus & Trash2 */}
                        <td className="px-3.5 py-2.5 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <button
                              type="button"
                              onClick={() => handleCloneSlot(slot)}
                              className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                              title="Nhân bản dòng này"
                              aria-label={`Nhân bản câu ${slot.slot_number}`}
                            >
                              <CopyPlus className="w-4 h-4 stroke-[1.5]" />
                            </button>

                            <button
                              type="button"
                              onClick={() => handleRemoveSlot(slot.slot_id)}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                              title="Xóa câu này"
                              aria-label={`Xóa câu ${slot.slot_number}`}
                            >
                              <Trash2 className="w-4 h-4 stroke-[1.5]" />
                            </button>
                          </div>
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

      {/* 3. Sticky Bottom Summary Bar (Thanh tổng kết điều khiển) */}
      <div className="fixed bottom-0 left-0 right-0 z-30 bg-white/95 backdrop-blur-md border-t border-slate-200 shadow-xl px-4 py-3">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Thông số tổng kết */}
          <div className="flex items-center gap-4 text-xs font-semibold flex-wrap">
            {/* Tổng câu */}
            <div className="flex items-center gap-1.5 text-slate-800">
              <TableProperties className="w-4 h-4 stroke-[1.75] text-blue-600" />
              <span>Tổng số: <strong className="tabular-nums text-sm font-bold">{totalSlotsCount}</strong> câu</span>
            </div>

            {/* Tổng điểm */}
            <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${
              isPointsBalanced 
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
                : 'bg-amber-50 text-amber-800 border-amber-200'
            }`}>
              {isPointsBalanced ? (
                <CheckCircle2 className="w-4 h-4 stroke-[1.75] text-emerald-600" />
              ) : (
                <AlertTriangle className="w-4 h-4 stroke-[1.75] text-amber-600" />
              )}
              <span>Điểm: <strong className="tabular-nums font-bold">{totalPoints.toFixed(2)} / 10.00đ</strong></span>
            </div>

            {/* Phân bổ nhận thức */}
            <div className="hidden md:flex items-center gap-2 text-[11px] text-slate-500 tabular-nums">
              <span>NB: <strong className="text-emerald-700">{pctNB}%</strong></span>
              <span>•</span>
              <span>TH: <strong className="text-blue-700">{pctTH}%</strong></span>
              <span>•</span>
              <span>VD: <strong className="text-amber-700">{pctVD}%</strong></span>
              <span>•</span>
              <span>VDC: <strong className="text-rose-700">{pctVDC}%</strong></span>
            </div>
          </div>

          {/* CTA Chính */}
          <button
            type="button"
            onClick={onStartGenerate}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs md:text-sm font-bold rounded-xl shadow-md transition-colors"
          >
            <Sparkles className="w-4 h-4 stroke-[1.75]" />
            <span>Bắt đầu sinh đề</span>
            <ArrowRight className="w-4 h-4 stroke-[1.75]" />
          </button>
        </div>
      </div>
    </div>
  );
};
