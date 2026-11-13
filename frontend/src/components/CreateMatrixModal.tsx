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
  const [slots, setSlots] = useState<ExamSlot[]>([]);
  const [preset, setPreset] = useState<ExamMatrix | null>(null);
  const [loadError, setLoadError] = useState('');

  React.useEffect(() => {
    if (!isOpen) return;
    const controller = new AbortController();
    const params = new URLSearchParams({ grade: String(grade), semester });
    async function loadPreset() {
      try {
        const response = await fetch(`/api/matrix/library?${params}`, { signal: controller.signal });
        if (!response.ok) throw new Error();
        const matrices: ExamMatrix[] = await response.json();
        if (controller.signal.aborted) return;
        const match = matrices.find(matrix =>
          !matrix.is_custom && matrix.grade === grade && matrix.semester === semester
        );
        setPreset(match ?? null);
        setLoadError(match ? '' : 'Chưa có mẫu cho lớp và kỳ này.');
      } catch {
        if (!controller.signal.aborted) setLoadError('Không tải được chủ đề. Hãy đóng và mở lại hộp thoại để thử lại.');
      }
    }
    void loadPreset();
    return () => controller.abort();
  }, [isOpen, grade, semester]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const topics = new Map<string, Set<string>>();
  for (const slot of preset?.slots ?? []) {
    if (!topics.has(slot.topic)) topics.set(slot.topic, new Set());
    if (slot.subtopic) topics.get(slot.topic)?.add(slot.subtopic);
  }

  const changeScope = (nextGrade: number, nextSemester: string) => {
    setGrade(nextGrade);
    setSemester(nextSemester);
    setPreset(null);
    setLoadError('');
    setSlots(previous => previous.map(slot => ({ ...slot, topic: '', subtopic: '' })));
  };

  const handleAddSlot = (part: number, forcedType?: ExamSlot["type"]) => {
    const newNum = slots.length + 1;
    const newType = forcedType || (part === 1 ? "MULTIPLE_CHOICE" : part === 2 ? "TRUE_FALSE" : part === 3 ? "SHORT_ANSWER" : "ESSAY");
    const defaultPoints = newType === "MULTIPLE_CHOICE" ? 0.25 : newType === "SHORT_ANSWER" ? 0.5 : 1.0;

    setSlots([
      ...slots,
      {
        slot_id: `slot_${Date.now()}_${newNum}`,
        slot_number: newNum,
        part: part,
        type: newType,
        topic: "",
        subtopic: "",
        level: "THONG_HIEU",
        points: defaultPoints
      }
    ]);
  };

  const handleRemoveSlot = (id: string) => {
    setSlots(slots.filter(s => s.slot_id !== id).map((s, idx) => ({ ...s, slot_number: idx + 1 })));
  };

  const handleSlotChange = (id: string, field: keyof ExamSlot, val: any) => {
    setSlots(previous => previous.map(s => s.slot_id === id ? {
      ...s, [field]: val, ...(field === 'topic' ? { subtopic: '' } : {})
    } : s));
  };

  const totalPoints = slots.reduce((sum, s) => sum + (Number(s.points) || 0), 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!preset || !slots.length || slots.some(slot => !slot.topic || !slot.subtopic)) return;
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
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in duration-200 overscroll-contain">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            <h3 id="create-matrix-title" className="font-bold text-slate-900 text-lg">Tự Thiết Kế Ma Trận Đề Thi Mới</h3>
          </div>
          <button 
            type="button"
            onClick={onClose} 
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Đóng hộp thoại tạo ma trận"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6 overscroll-contain">
          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label htmlFor="matrix-title-input" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Tên ma trận / Tiêu đề kỳ thi *
              </label>
              <input
                id="matrix-title-input"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="VD: ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - KHỐI 12"
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="matrix-grade-select" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Khối Lớp
              </label>
              <select
                id="matrix-grade-select"
                value={grade}
                onChange={(e) => {
                  const nextGrade = Number(e.target.value);
                  changeScope(nextGrade, nextGrade !== 12 && semester === 'Tốt nghiệp THPT' ? 'Học kỳ 1' : semester);
                }}
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 bg-white"
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
              <label htmlFor="matrix-semester-select" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Học kỳ / Đợt thi
              </label>
              <select
                id="matrix-semester-select"
                value={semester}
                onChange={(e) => changeScope(grade, e.target.value)}
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 bg-white"
              >
                <option value="Giữa kỳ 1">Giữa kỳ 1</option>
                <option value="Học kỳ 1">Cuối kỳ 1</option>
                <option value="Giữa kỳ 2">Giữa kỳ 2</option>
                <option value="Học kỳ 2">Cuối kỳ 2</option>
                {grade === 12 && <option value="Tốt nghiệp THPT">Tốt nghiệp THPT</option>}
              </select>
            </div>

            <div>
              <label htmlFor="matrix-time-input" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Thời gian làm bài (phút)
              </label>
              <input
                id="matrix-time-input"
                type="number"
                min={15}
                max={180}
                value={timeMinutes}
                onChange={(e) => setTimeMinutes(Number(e.target.value))}
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="matrix-desc-input" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Mô tả ngắn
              </label>
              <input
                id="matrix-desc-input"
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="VD: Kiểm tra chuyên đề Đạo hàm & Hình không gian"
                className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              />
            </div>
          </div>

          {/* Slots Table */}
          <div className="space-y-3">
            {!preset && <p role="status" className="text-sm text-slate-600">{loadError || 'Đang tải chủ đề và dạng bài…'}</p>}
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Danh sách câu hỏi ({slots.length} câu)
              </span>
              <div className="flex flex-wrap gap-1.5">
                <button type="button" disabled={!preset || slots.length > 0}
                  onClick={() => preset && setSlots(preset.slots.map(slot => ({ ...slot })))}
                  className="px-2.5 py-1 text-xs font-semibold rounded border border-slate-300 disabled:opacity-50">
                  Dùng ma trận mẫu
                </button>
                <button
                  type="button"
                  onClick={() => handleAddSlot(1, "MULTIPLE_CHOICE")}
                  className="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 rounded border border-blue-200"
                >
                  + TN 4 lựa chọn (0.25đ)
                </button>
                <button
                  type="button"
                  onClick={() => handleAddSlot(2, "TRUE_FALSE")}
                  className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded border border-emerald-200"
                >
                  + Đúng / Sai (1.0đ)
                </button>
                <button
                  type="button"
                  onClick={() => handleAddSlot(3, "SHORT_ANSWER")}
                  className="px-2.5 py-1 text-xs font-semibold bg-amber-50 text-amber-700 hover:bg-amber-100 rounded border border-amber-200"
                >
                  + Trả lời ngắn (0.5đ)
                </button>
                <button
                  type="button"
                  onClick={() => handleAddSlot(slots.length > 0 ? (matrix => (slots.some(s => s.type === "ESSAY") ? slots.find(s => s.type === "ESSAY")!.part : Math.max(...slots.map(s => s.part)) + 1))(slots) : 2, "ESSAY")}
                  className="px-2.5 py-1 text-xs font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 rounded border border-purple-200"
                >
                  + Tự luận (1.0đ)
                </button>
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden max-h-72 overflow-y-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
                  <tr>
                    <th className="p-2 w-10 text-center">STT</th>
                    <th className="p-2 w-16 text-center">Phần</th>
                    <th className="p-2 w-36">Dạng thức</th>
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
                      <td className="p-2 text-center">
                        <input
                          type="number"
                          min={1}
                          max={5}
                          value={s.part}
                          onChange={(e) => handleSlotChange(s.slot_id, 'part', parseInt(e.target.value) || 1)}
                          className="w-12 text-center p-1 border rounded bg-white"
                        />
                      </td>
                      <td className="p-2">
                        <select
                          aria-label={`Dạng thức cho câu ${idx + 1}`}
                          value={s.type}
                          onChange={(e) => {
                            const t = e.target.value as ExamSlot["type"];
                            handleSlotChange(s.slot_id, 'type', t);
                            if (t === 'MULTIPLE_CHOICE') handleSlotChange(s.slot_id, 'points', 0.25);
                            else if (t === 'SHORT_ANSWER') handleSlotChange(s.slot_id, 'points', 0.5);
                            else handleSlotChange(s.slot_id, 'points', 1.0);
                          }}
                          className="w-full p-1 border rounded bg-white focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 font-medium"
                        >
                          <option value="MULTIPLE_CHOICE">Trắc nghiệm</option>
                          <option value="TRUE_FALSE">Đúng / Sai</option>
                          <option value="SHORT_ANSWER">Trả lời ngắn</option>
                          <option value="ESSAY">Tự luận</option>
                        </select>
                      </td>
                      <td className="p-2">
                        <select
                          required
                          disabled={!preset}
                          aria-label={`Chủ đề cho câu ${idx + 1}`}
                          value={s.topic}
                          onChange={(e) => handleSlotChange(s.slot_id, 'topic', e.target.value)}
                          className="w-full p-1 border rounded focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
                        >
                          <option value="">Chọn chủ đề</option>
                          {[...topics.keys()].map(topic => <option key={topic}>{topic}</option>)}
                        </select>
                      </td>
                      <td className="p-2">
                        <select
                          required
                          disabled={!preset || !s.topic}
                          aria-label={`Dạng bài chi tiết cho câu ${idx + 1}`}
                          value={s.subtopic || ''}
                          onChange={(e) => handleSlotChange(s.slot_id, 'subtopic', e.target.value)}
                          className="w-full p-1 border rounded focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
                        >
                          <option value="">Chọn dạng bài</option>
                          {[...(topics.get(s.topic) ?? [])].map(subtopic => <option key={subtopic}>{subtopic}</option>)}
                        </select>
                      </td>
                      <td className="p-2">
                        <select
                          aria-label={`Mức độ nhận thức cho câu ${idx + 1}`}
                          value={s.level}
                          onChange={(e) => handleSlotChange(s.slot_id, 'level', e.target.value)}
                          className="w-full p-1 border rounded bg-white focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
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
                          aria-label={`Điểm số cho câu ${idx + 1}`}
                          value={s.points}
                          onChange={(e) => handleSlotChange(s.slot_id, 'points', parseFloat(e.target.value) || 0)}
                          className="w-14 p-1 border rounded text-center focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
                        />
                      </td>
                      <td className="p-2 text-center">
                        <button
                          type="button"
                          aria-label={`Xóa câu ${idx + 1}`}
                          onClick={() => handleRemoveSlot(s.slot_id)}
                          className="text-slate-400 hover:text-rose-600 focus:outline-none focus-visible:ring-1 focus-visible:ring-rose-500 rounded p-1"
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
              disabled={!preset || !slots.length || slots.some(slot => !slot.topic || !slot.subtopic)}
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
