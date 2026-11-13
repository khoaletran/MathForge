import React, { useState, useEffect } from 'react';
import { Key, Shield, Check, X, Server } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiKey: string;
  onSaveApiKey: (key: string) => void;
  systemHealth: any;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  apiKey,
  onSaveApiKey,
  systemHealth
}) => {
  const [inputKey, setInputKey] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveApiKey(inputKey.trim());
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 1000);
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overscroll-contain"
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-dialog-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in duration-200 overscroll-contain">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-indigo-600" />
            <h3 id="settings-dialog-title" className="font-bold text-slate-900 text-lg">Cấu hình API & Hệ thống</h3>
          </div>
          <button 
            type="button"
            onClick={onClose} 
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            aria-label="Đóng bảng cấu hình"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Gemini API Key */}
          <div>
            <label htmlFor="gemini-api-key" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Gemini API Key (Google AI Studio)
            </label>
            <input
              id="gemini-api-key"
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              placeholder="AIzaSy…"
              className="w-full text-sm font-mono p-3 border border-slate-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            />
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              * Khóa API được lưu cục bộ trên trình duyệt của bạn (localStorage).
              Nếu để trống, hệ thống sẽ tự động dùng <strong>Chế độ Ngân hàng câu hỏi mẫu (Offline Mutation Generator)</strong>.
            </p>
          </div>

          {/* System status info */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
            <span className="font-bold text-slate-700 flex items-center gap-1.5 mb-2">
              <Server className="w-4 h-4 text-slate-500" /> Trạng thái hạ tầng
            </span>

            <div className="flex items-center justify-between">
              <span className="text-slate-600">Backend Core (FastAPI):</span>
              <span className="font-semibold text-emerald-600">Đang hoạt động (Online)</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-600">Bộ kiểm chứng toán học (SymPy):</span>
              <span className="font-semibold text-emerald-600">v{systemHealth?.sympy_version || '1.14'}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-600">Chuẩn tài liệu:</span>
              <span className="font-semibold text-indigo-600">ex_test.sty & GDPT 2018</span>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            {saved ? <Check className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
            <span>{saved ? 'Đã lưu thành công!' : 'Lưu cấu hình'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
