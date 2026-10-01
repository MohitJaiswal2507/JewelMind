import React, { useState } from 'react';
import { X, ShieldCheck, AlertTriangle } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import {
  DefectSeverity,
  QualityCheckCreate,
  QualityCheckResult,
} from '../../../types/execution';

interface QualityCheckDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stepNumber?: number | null;
  stageName?: string | null;
  qualityCheckpoint?: string | null;
  onSubmit: (payload: QualityCheckCreate) => Promise<void>;
}

export const QualityCheckDialog: React.FC<QualityCheckDialogProps> = ({
  isOpen,
  onClose,
  stepNumber,
  stageName,
  qualityCheckpoint,
  onSubmit,
}) => {
  const [result, setResult] = useState<QualityCheckResult>('PASS');
  const [defectSeverity, setDefectSeverity] = useState<DefectSeverity>('NONE');
  const [defectType, setDefectType] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleResultChange = (newResult: QualityCheckResult) => {
    setResult(newResult);
    if (newResult === 'PASS') {
      setDefectSeverity('NONE');
    } else if (defectSeverity === 'NONE') {
      setDefectSeverity('MEDIUM');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (result === 'PASS' && (defectSeverity === 'HIGH' || defectSeverity === 'CRITICAL')) {
      setError('Cannot record PASS with HIGH or CRITICAL defect severity.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        result,
        defect_severity: defectSeverity,
        defect_type: defectType.trim() || undefined,
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Quality inspection submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-white/[0.1] bg-[#0E111A] p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-serif font-bold text-white">Record Quality Inspection</h2>
              <p className="text-xs text-slate-400 font-light">
                Step {stepNumber ?? '-'}: <strong className="text-slate-200">{stageName || 'Operation'}</strong>
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0 rounded-lg text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {qualityCheckpoint && (
          <div className="mt-3 p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs text-amber-200">
            <span className="font-semibold text-amber-400">QC Specification: </span>
            {qualityCheckpoint}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Inspection Outcome
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['PASS', 'FAIL', 'REWORK'] as QualityCheckResult[]).map((r) => {
                const isSelected = result === r;
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => handleResultChange(r)}
                    className={`py-3 px-3 rounded-xl border text-xs font-bold transition-all ${
                      isSelected
                        ? r === 'PASS'
                          ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 shadow-md shadow-emerald-500/10'
                          : r === 'FAIL'
                          ? 'bg-rose-500/20 border-rose-400 text-rose-300 shadow-md shadow-rose-500/10'
                          : 'bg-amber-500/20 border-amber-400 text-amber-300 shadow-md shadow-amber-500/10'
                        : 'bg-white/[0.02] border-white/[0.08] text-slate-400 hover:bg-white/[0.05]'
                    }`}
                  >
                    {r}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Defect Severity
            </label>
            <select
              value={defectSeverity}
              onChange={(e) => setDefectSeverity(e.target.value as DefectSeverity)}
              className="w-full px-3 py-2 rounded-xl bg-[#111625] border border-white/10 text-sm text-slate-200 focus:outline-none focus:border-amber-400/50"
            >
              <option value="NONE">NONE (Zero Defects)</option>
              <option value="LOW">LOW (Cosmetic, negligible)</option>
              <option value="MEDIUM">MEDIUM (Minor, reworkable)</option>
              <option value="HIGH">HIGH (Major structural/aesthetic)</option>
              <option value="CRITICAL">CRITICAL (Total rejection)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Defect Code / Type (Optional)
            </label>
            <Input
              placeholder="e.g. POROSITY, MISALIGNMENT, SCRATCH"
              value={defectType}
              onChange={(e) => setDefectType(e.target.value)}
              className="bg-[#111625] border-white/10 text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Inspector Notes (Optional)
            </label>
            <Textarea
              placeholder="Provide context on inspection verdict or rework guidelines..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="bg-[#111625] border-white/10 text-xs h-20"
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-white/[0.08]">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              size="sm"
              disabled={loading}
            >
              {loading ? 'Submitting...' : 'Log Inspection Outcome'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
