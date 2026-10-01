import React, { useState } from 'react';
import { X, PackagePlus, AlertTriangle } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { MaterialConsumptionCreate } from '../../../types/execution';

interface MaterialConsumptionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stepNumber?: number | null;
  stageName?: string | null;
  onSubmit: (payload: MaterialConsumptionCreate) => Promise<void>;
}

export const MaterialConsumptionDialog: React.FC<MaterialConsumptionDialogProps> = ({
  isOpen,
  onClose,
  stepNumber,
  stageName,
  onSubmit,
}) => {
  const [materialType, setMaterialType] = useState<string>('gold_18k');
  const [materialName, setMaterialName] = useState<string>('18K Yellow Gold Grain');
  const [unit, setUnit] = useState<string>('g');
  const [actualQuantity, setActualQuantity] = useState<string>('');
  const [plannedQuantity, setPlannedQuantity] = useState<string>('');
  const [wastageQuantity, setWastageQuantity] = useState<string>('0');
  const [wastageReason, setWastageReason] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const actual = parseFloat(actualQuantity);
    const planned = plannedQuantity ? parseFloat(plannedQuantity) : undefined;
    const wastage = wastageQuantity ? parseFloat(wastageQuantity) : 0;

    if (isNaN(actual) || actual <= 0) {
      setError('Actual quantity must be a positive number.');
      return;
    }

    if (isNaN(wastage) || wastage < 0) {
      setError('Wastage quantity cannot be negative.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        material_type: materialType,
        material_name: materialName,
        unit,
        actual_quantity: actual,
        planned_quantity: planned,
        wastage_quantity: wastage,
        wastage_reason: wastageReason.trim() || undefined,
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to record consumption');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-white/[0.1] bg-[#0E111A] p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-300">
              <PackagePlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-serif font-bold text-white">Log Material & Scrap</h2>
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

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Material Type
              </label>
              <select
                value={materialType}
                onChange={(e) => {
                  setMaterialType(e.target.value);
                  if (e.target.value.includes('gold')) {
                    setMaterialName(e.target.value.toUpperCase() + ' Alloy');
                    setUnit('g');
                  } else if (e.target.value.includes('diamond')) {
                    setMaterialName('Round Brilliant Diamond');
                    setUnit('ct');
                  }
                }}
                className="w-full px-3 py-2 rounded-xl bg-[#111625] border border-white/10 text-xs text-slate-200 focus:outline-none focus:border-amber-400/50"
              >
                <option value="gold_18k">18K Gold</option>
                <option value="gold_14k">14K Gold</option>
                <option value="platinum_950">950 Platinum</option>
                <option value="silver_925">925 Sterling Silver</option>
                <option value="diamond">Natural Diamond</option>
                <option value="sapphire">Blue Sapphire</option>
                <option value="emerald">Emerald</option>
                <option value="consumable">Solder / Consumable</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Unit of Measure
              </label>
              <Input
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="g, ct, pcs"
                className="bg-[#111625] border-white/10 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Material Name / Batch Description
            </label>
            <Input
              value={materialName}
              onChange={(e) => setMaterialName(e.target.value)}
              placeholder="e.g. 18K Yellow Gold Grain #A12"
              className="bg-[#111625] border-white/10 text-xs"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Actual Net ({unit})
              </label>
              <Input
                type="number"
                step="any"
                required
                value={actualQuantity}
                onChange={(e) => setActualQuantity(e.target.value)}
                placeholder="8.35"
                className="bg-[#111625] border-white/10 text-xs font-mono font-bold text-amber-300"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Planned ({unit})
              </label>
              <Input
                type="number"
                step="any"
                value={plannedQuantity}
                onChange={(e) => setPlannedQuantity(e.target.value)}
                placeholder="8.20"
                className="bg-[#111625] border-white/10 text-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Wastage / Scrap
              </label>
              <Input
                type="number"
                step="any"
                value={wastageQuantity}
                onChange={(e) => setWastageQuantity(e.target.value)}
                placeholder="0.15"
                className="bg-[#111625] border-white/10 text-xs font-mono text-rose-300"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Wastage / Scrap Classification (Optional)
            </label>
            <Input
              placeholder="e.g. Filing dust, sprue cutoff, casting flash"
              value={wastageReason}
              onChange={(e) => setWastageReason(e.target.value)}
              className="bg-[#111625] border-white/10 text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Artisan Notes (Optional)
            </label>
            <Textarea
              placeholder="Crucible run details or alloy scale measurement notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="bg-[#111625] border-white/10 text-xs h-16"
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-white/[0.08]">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              size="sm"
              disabled={loading}
            >
              {loading ? 'Logging...' : 'Confirm Material Entry'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
