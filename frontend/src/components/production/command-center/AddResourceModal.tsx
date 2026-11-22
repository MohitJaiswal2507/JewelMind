import React, { useState } from 'react';
import {
  X,
  UserCheck,
  Cpu,
  Loader2,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { WORKER_SKILLS, MACHINE_TYPES } from '../../../types/production';
import { productionService } from '../../../services/api/productionService';

interface AddResourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'worker' | 'machine';
  onSuccess: () => void;
  showFeedback: (msg: string, type?: 'success' | 'error') => void;
}

export const AddResourceModal: React.FC<AddResourceModalProps> = ({
  isOpen,
  onClose,
  type,
  onSuccess,
  showFeedback,
}) => {
  const isWorker = type === 'worker';
  const [name, setName] = useState<string>('');
  const [skillOrType, setSkillOrType] = useState<string>(
    isWorker ? WORKER_SKILLS[0].value : MACHINE_TYPES[0].value
  );
  const [capacity, setCapacity] = useState<number>(8);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError(`Please provide a ${isWorker ? 'Karigar name' : 'Equipment name'}.`);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      if (isWorker) {
        await productionService.createWorker({
          name: name.trim(),
          skill: skillOrType,
          capacity_hours_per_day: Number(capacity) || 8,
          is_available: true,
        });
        showFeedback(`Registered Karigar: ${name.trim()}`);
      } else {
        await productionService.createMachine({
          name: name.trim(),
          machine_type: skillOrType,
          capacity_hours_per_day: Number(capacity) || 8,
          is_available: true,
        });
        showFeedback(`Registered Equipment: ${name.trim()}`);
      }
      setName('');
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to register resource';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md rounded-2xl border border-white/[0.1] bg-[#0E111A] p-6 shadow-2xl space-y-4 text-slate-200">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-center justify-center">
              {isWorker ? <UserCheck className="w-4 h-4" /> : <Cpu className="w-4 h-4" />}
            </div>
            <div>
              <h3 className="text-base font-serif font-bold text-white">
                {isWorker ? 'Register New Karigar' : 'Register Equipment'}
              </h3>
              <p className="text-[11px] text-slate-400 font-light">
                {isWorker
                  ? 'Add a master artisan to workshop bench capacity'
                  : 'Add machinery or tool to workshop duty cycle'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.05] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">
              {isWorker ? 'Artisan Full Name' : 'Equipment Name & Model'}
            </label>
            <Input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={isWorker ? 'e.g. Ramesh Verma' : 'e.g. Asiga Max 3D Wax Printer'}
              className="bg-[#141926] border-white/10 text-white text-xs h-9"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">
              {isWorker ? 'Primary Craft Specialization' : 'Machine Classification'}
            </label>
            <select
              value={skillOrType}
              onChange={(e) => setSkillOrType(e.target.value)}
              className="w-full bg-[#141926] border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-amber-400/50"
            >
              {isWorker
                ? WORKER_SKILLS.map((s) => (
                    <option key={s.value} value={s.value} className="bg-[#0E111A]">
                      {s.label}
                    </option>
                  ))
                : MACHINE_TYPES.map((m) => (
                    <option key={m.value} value={m.value} className="bg-[#0E111A]">
                      {m.label}
                    </option>
                  ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300">
              {isWorker ? 'Daily Bench Hours (Capacity)' : 'Daily Operational Duty (Hours)'}
            </label>
            <Input
              type="number"
              min="1"
              max="24"
              step="0.5"
              required
              value={capacity}
              onChange={(e) => setCapacity(Number(e.target.value) || 8)}
              className="bg-[#141926] border-white/10 text-white text-xs h-9"
            />
          </div>

          <div className="flex items-center justify-end space-x-2 pt-3 border-t border-white/[0.08]">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={submitting}
              className="text-xs border-[#1E2333]"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              size="sm"
              disabled={submitting}
              className="text-xs font-semibold"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>{isWorker ? 'Register Karigar' : 'Register Equipment'}</span>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
