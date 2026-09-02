import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '../ui/button';

interface ClearCanvasModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const ClearCanvasModal: React.FC<ClearCanvasModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="w-full max-w-md bg-[#0b0f19] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Clear Drawing Canvas?</h2>
            <p className="text-xs text-slate-400">All unsaved artwork on this surface will be erased.</p>
          </div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Are you sure you want to clear your current jewellery sketch? You can still use Undo (Ctrl+Z) immediately after clearing if you change your mind.
        </p>

        <div className="flex items-center justify-end space-x-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            className="border-slate-700 text-xs"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className="font-semibold text-xs min-w-[100px]"
          >
            Clear Canvas
          </Button>
        </div>
      </div>
    </div>
  );
};
