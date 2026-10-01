import React, { useState } from 'react';
import { X, Cpu, AlertTriangle } from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { Machine } from '../../../types/production';

interface MachineAssignmentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  machines: Machine[];
  currentMachineId: string | null;
  requiredMachineType?: string | null;
  onAssign: (machineId: string) => Promise<void>;
}

export const MachineAssignmentDialog: React.FC<MachineAssignmentDialogProps> = ({
  isOpen,
  onClose,
  machines,
  currentMachineId,
  requiredMachineType,
  onAssign,
}) => {
  const [selectedMachineId, setSelectedMachineId] = useState<string>(currentMachineId || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMachineId) return;

    setLoading(true);
    setError(null);
    try {
      await onAssign(selectedMachineId);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to assign equipment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-white/[0.1] bg-[#0E111A] p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-300">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-serif font-bold text-white">Assign Workshop Equipment</h2>
              <p className="text-xs text-slate-400 font-light">
                Required Equipment: <strong className="text-purple-200">{requiredMachineType || 'Workbench / Manual Station'}</strong>
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

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
            {machines.map((machine) => {
              const isCompatible =
                !requiredMachineType ||
                machine.machine_type.toLowerCase() === requiredMachineType.toLowerCase() ||
                machine.machine_type.toLowerCase().includes(requiredMachineType.toLowerCase()) ||
                requiredMachineType.toLowerCase().includes(machine.machine_type.toLowerCase());

              const isSelected = selectedMachineId === machine.id;

              return (
                <div
                  key={machine.id}
                  onClick={() => setSelectedMachineId(machine.id)}
                  className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? 'bg-purple-500/10 border-purple-500/50 shadow-md shadow-purple-500/5'
                      : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04]'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <input
                      type="radio"
                      name="equipment"
                      checked={isSelected}
                      onChange={() => setSelectedMachineId(machine.id)}
                      className="accent-purple-400 cursor-pointer"
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-semibold text-white">{machine.name}</span>
                        {isCompatible ? (
                          <Badge variant="success" className="text-[9px] py-0 px-1">
                            Compatible
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="text-[9px] py-0 px-1">
                            Type Incompatible
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-400">
                        Type: <span className="text-slate-300 font-medium">{machine.machine_type}</span> &bull; {machine.capacity_hours_per_day}h/day
                      </p>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                      machine.is_available
                        ? 'text-emerald-400 bg-emerald-500/10'
                        : 'text-rose-400 bg-rose-500/10'
                    }`}
                  >
                    {machine.is_available ? 'Ready' : 'Maintenance'}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-white/[0.08]">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              size="sm"
              disabled={!selectedMachineId || loading}
            >
              {loading ? 'Assigning...' : 'Confirm Equipment Assignment'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
