import React, { useState } from 'react';
import { X, Plus, Trash2, Check, Layers, AlertCircle } from 'lucide-react';
import { ExamMatrix, ExamSlot } from './MatrixManager';

interface CreateMatrixModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newMatrix: ExamMatrix) => Promise<void>;
}

export const CreateMatrixModal: React.FC<CreateMatrixModalProps> = ({
  isOpen,
  onClose,
  onSave
}) => {
  const [title, setTitle] = useState('');
  const [grade, setGrade] = useState<number>(12);
  const [semester, setSemester] = useState<string>('Học kỳ 1');
  const [timeMinutes, setTimeMinutes] = useState<number>(90);
  const [description, setDescription] = useState('');
  const [slots, setSlots] = useState<ExamSlot[]>([
    {
      slot_id: `slot_${Date.now()}_1`,
      slot_number: 1,
      part: 1,
      type: "MULTIPLE_CHOICE",
      topic: "Ứng dụng đạo hàm khảo sát hàm số",
      subtopic: "Tính đơn điệu của hàm số",
      level: "NHAN_BIET",
      points: 0.25
    },
    {
      slot_id: `slot_${Date.now()}_2`,
      slot_number: 2,
      part: 1,
      type: "MULTIPLE_CHOICE",
      topic: "Ứng dụng đạo hàm khảo sát hàm số",
      subtopic: "Cực trị của hàm số",
      level: "THONG_HIEU",
      points: 0.25
    },
    {
      slot_id: `slot_${Date.now()}_3`,
      slot_number: 3,
      part: 2,
      type: "TRUE_FALSE",
      topic: "Ứng dụng đạo hàm khảo sát hàm số",
      subtopic: "Khảo sát tính biến thiên và đồ thị",
      level: "THONG_HIEU",
      points: 1.0
    },
    {
      slot_id: `slot_${Date.now()}_4`,
      slot_number: 4,
      part: 3,
      type: "SHORT_ANSWER",
      topic: "Ứng dụng đạo hàm khảo sát hàm số",
      subtopic: "Bài toán tối ưu hóa thực tế",
      level: "VAN_DUNG",
      points: 0.5
    }
  ]);

  if (!isOpen) return null;

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  const handleAddSlot = (part: number) => {
    const newNum = slots.length + 1;
    const newType = part === 1 ? "MULTIPLE_CHOICE" : part === 2 ? "TRUE_FALSE" : "SHORT_ANSWER";
    const defaultPoints = part === 1 ? 0.25 : part === 2 ? 1.0 : 0.5;

    setSlots([
      ...slots,
      {
        slot_id: `slot_${Date.now()}_${newNum}`,
        slot_number: newNum,
        part: part,
        type: newType,
        topic: "Chủ đề Toán học",
        subtopic: "Dạng bài",
        level: "THONG_HIEU",
        points: defaultPoints
      }
    ]);
  };

  const handleRemoveSlot = (id: string) => {
    setSlots(slots.filter(s => s.slot_id !== id).map((s, idx) => ({ ...s, slot_number: idx + 1 })));
  };

  const handleSlotChange = (id: string, field: keyof ExamSlot, val: any) => {
    setSlots(slots.map(s => s.slot_id === id ? { ...s, [field]: val } : s));
  };

  const totalPoints = slots.reduce((sum, s) => sum + (Number(s.points) || 0), 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      alert("Vui lòng nhập tên đề thi / ma trận");
      return;
    }

    const newMatrix: ExamMatrix = {
      id: `custom_matrix_${Date.now()}`,
      title: title.trim(),
      description: description.trim() || `Ma trận tự thiết kế cho Lớp ${grade}`,
      subject: "TOÁN HỌC",
      grade: grade,
      semester: semester,
      time_minutes: timeMinutes,
      academic_year: "2025 - 2026",
      tags: [`Lớp ${grade}`, semester, "Ma trận tự tạo"],
      is_custom: true,
      slots: slots
    };

    await onSave(newMatrix);
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overscroll-contain"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-matrix-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in duration-200">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <h3 id="create-matrix-title" className="font-bold text-slate-900 text-lg">Tự Thiết Kế Ma Trận Đề Thi Mới</h3>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Đóng bảng thiết kế ma trận"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Tên ma trận / Tiêu đề kỳ thi *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="VD: ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - KHỐI 12"
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Khối Lớp
              </label>
              <select
                value={grade}
                onChange={(e) => setGrade(Number(e.target.value))}
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value={6}>Lớp 6</option>
                <option value={7}>Lớp 7</option>
                <option value={8}>Lớp 8</option>
                <option value={9}>Lớp 9 (Thi vào 10)</option>
                <option value={10}>Lớp 10</option>
                <option value={11}>Lớp 11</option>
                <option value={12}>Lớp 12 (Tốt nghiệp)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Học kỳ / Đợt thi
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              >
                <option value="Giữa kỳ 1">Giữa kỳ 1</option>
                <option value="Học kỳ 1">Cuối kỳ 1</option>
                <option value="Giữa kỳ 2">Giữa kỳ 2</option>
                <option value="Học kỳ 2">Cuối kỳ 2</option>
                <option value="Tốt nghiệp THPT">Tốt nghiệp THPT</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Thời gian làm bài (phút)
              </label>
              <input
                type="number"
                min={15}
                max={180}
                value={timeMinutes}
                onChange={(e) => setTimeMinutes(Number(e.target.value))}
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Mô tả ngắn
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="VD: Kiểm tra chuyên đề Đạo hàm & Hình không gian"
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Slots Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Danh sách câu hỏi ({slots.length} câu)
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleAddSlot(1)}
                  className="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 rounded border border-blue-200"
                >
                  + Thêm Phần I (TN)
                </button>
                <button
                  type="button"
                  onClick={() => handleAddSlot(2)}
                  className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded border border-emerald-200"
                >
                  + Thêm Phần II (Đ/S)
                </button>
                <button
                  type="button"
                  onClick={() => handleAddSlot(3)}
                  className="px-2.5 py-1 text-xs font-semibold bg-amber-50 text-amber-700 hover:bg-amber-100 rounded border border-amber-200"
                >
                  + Thêm Phần III (Ngắn)
                </button>
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden max-h-72 overflow-y-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
                  <tr>
                    <th className="p-2 w-10 text-center">STT</th>
                    <th className="p-2 w-28">Phần thi</th>
                    <th className="p-2">Chủ đề</th>
                    <th className="p-2">Dạng bài</th>
                    <th className="p-2 w-28">Mức độ</th>
                    <th className="p-2 w-16 text-center">Điểm</th>
                    <th className="p-2 w-10 text-center">Xóa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {slots.map((s, idx) => (
                    <tr key={s.slot_id} className="hover:bg-slate-50">
                      <td className="p-2 font-bold text-center">{idx + 1}</td>
                      <td className="p-2">
                        <select
                          value={s.part}
                          onChange={(e) => {
                            const p = Number(e.target.value);
                            handleSlotChange(s.slot_id, 'part', p);
                            handleSlotChange(s.slot_id, 'type', p === 1 ? 'MULTIPLE_CHOICE' : p === 2 ? 'TRUE_FALSE' : 'SHORT_ANSWER');
                          }}
                          className="w-full p-1 border rounded bg-white"
                        >
                          <option value={1}>Phần I (TN)</option>
                          <option value={2}>Phần II (Đ/S)</option>
                          <option value={3}>Phần III (Ngắn)</option>
                        </select>
                      </td>
                      <td className="p-2">
                        <input
                          type="text"
                          value={s.topic}
                          onChange={(e) => handleSlotChange(s.slot_id, 'topic', e.target.value)}
                          className="w-full p-1 border rounded"
                        />
                      </td>
                      <td className="p-2">
                        <input
                          type="text"
                          value={s.subtopic || ''}
                          onChange={(e) => handleSlotChange(s.slot_id, 'subtopic', e.target.value)}
                          className="w-full p-1 border rounded"
                        />
                      </td>
                      <td className="p-2">
                        <select
                          value={s.level}
                          onChange={(e) => handleSlotChange(s.slot_id, 'level', e.target.value)}
                          className="w-full p-1 border rounded bg-white"
                        >
                          <option value="NHAN_BIET">Nhận biết</option>
                          <option value="THONG_HIEU">Thông hiểu</option>
                          <option value="VAN_DUNG">Vận dụng</option>
                          <option value="VAN_DUNG_CAO">Vận dụng cao</option>
                        </select>
                      </td>
                      <td className="p-2 text-center">
                        <input
                          type="number"
                          step={0.1}
                          value={s.points}
                          onChange={(e) => handleSlotChange(s.slot_id, 'points', parseFloat(e.target.value) || 0)}
                          className="w-14 p-1 border rounded text-center"
                        />
                      </td>
                      <td className="p-2 text-center">
                        <button
                          type="button"
                          onClick={() => handleRemoveSlot(s.slot_id)}
                          className="text-slate-400 hover:text-rose-600"
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

          {/* Sticky Summary */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
            <div>
              Tổng số câu: <strong className="text-slate-900">{slots.length} câu</strong> • 
              Tổng điểm: <strong className={Math.abs(totalPoints - 10) < 0.01 ? "text-emerald-600 font-bold" : "text-amber-600 font-bold"}>
                {totalPoints.toFixed(2)} / 10 điểm
              </strong>
            </div>
            {Math.abs(totalPoints - 10) > 0.01 && (
              <span className="text-amber-600 flex items-center gap-1 font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> Chưa khớp thang điểm 10 chuẩn
              </span>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
            >
              Hủy
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition"
            >
              <Check className="w-4 h-4" />
              Lưu & Chọn ma trận này
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
