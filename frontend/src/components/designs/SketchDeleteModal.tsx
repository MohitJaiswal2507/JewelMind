import React, { useState } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';

interface SketchDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  designName?: string;
}

export const SketchDeleteModal: React.FC<SketchDeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  designName,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDelete = async () => {
    setLoading(true);
    setError(null);
    try {
      await onConfirm();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete sketch asset.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md bg-[#0E111A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden p-6 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-serif text-lg font-medium text-white tracking-tight">Delete Sketch Blueprint?</h2>
            <p className="text-xs text-slate-400 font-light">This action cannot be undone.</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 space-y-1.5 text-xs">
          <div className="text-slate-400 font-light">Target Blueprint:</div>
          <div className="text-sm font-semibold text-white truncate">{designName || 'Jewellery Design'}</div>
          <p className="text-[11px] text-slate-500 pt-1 font-light">
            The sketch asset will be permanently purged from cloud storage. The design record and metadata will remain intact.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end space-x-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={loading}
            className="border-white/10"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={loading}
            className="min-w-[100px] font-semibold"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Deleting...</span>
              </div>
            ) : (
              'Delete Sketch'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
