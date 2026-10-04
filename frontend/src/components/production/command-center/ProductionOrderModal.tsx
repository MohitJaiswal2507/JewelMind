import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Design } from '../../../types/design';
import { OrderPriority, ORDER_PRIORITIES } from '../../../types/production';

interface ProductionOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  designs: Design[];
  onSubmit: (data: {
    design_id: string;
    quantity: number;
    priority: OrderPriority;
    deadline: string;
    notes?: string;
  }) => Promise<void>;
  loading?: boolean;
}

export const ProductionOrderModal: React.FC<ProductionOrderModalProps> = ({
  isOpen,
  onClose,
  designs,
  onSubmit,
  loading = false,
}) => {
  const [selectedDesignId, setSelectedDesignId] = useState<string>(designs[0]?.id || '');
  const [quantity, setQuantity] = useState<number>(1);
  const [priority, setPriority] = useState<OrderPriority>('medium');
  const [deadline, setDeadline] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    return d.toISOString().split('T')[0];
  });
  const [notes, setNotes] = useState<string>('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDesignId) return;

    await onSubmit({
      design_id: selectedDesignId,
      quantity,
      priority,
      deadline: new Date(deadline).toISOString(),
      notes: notes.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-[#0E111A] border border-white/[0.1] rounded-2xl shadow-2xl overflow-hidden space-y-5 p-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
              <Plus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-serif font-bold text-white">Create Production Order</h3>
              <p className="text-xs text-slate-400 font-light">Dispatch an approved fine jewellery design to atelier production</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Select Design */}
          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">Select Approved Design</label>
            <select
              value={selectedDesignId}
              onChange={(e) => setSelectedDesignId(e.target.value)}
              className="w-full h-9 rounded-lg bg-[#121624] border border-white/[0.08] text-white px-3 text-xs focus:border-amber-400/50"
              required
            >
              {designs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.category || 'Jewellery'})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Quantity */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Manufacturing Quantity</label>
              <Input
                type="number"
                min={1}
                max={500}
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                className="bg-[#121624] border-white/[0.08] text-white font-mono h-9"
                required
              />
            </div>

            {/* Priority */}
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Order Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as OrderPriority)}
                className="w-full h-9 rounded-lg bg-[#121624] border border-white/[0.08] text-white px-3 text-xs capitalize focus:border-amber-400/50"
              >
                {ORDER_PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Delivery Deadline */}
          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">Target Delivery Date</label>
            <Input
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="bg-[#121624] border-white/[0.08] text-white font-mono h-9"
              required
            />
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">Atelier Dispatch Notes (Optional)</label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Hallmarking required at Mumbai centre; urgent pavé stone setting."
              className="bg-[#121624] border-white/[0.08] text-white text-xs h-20"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-2 pt-3 border-t border-white/[0.08]">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs border-[#1E2333] text-slate-300"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gold"
              size="sm"
              disabled={loading || !selectedDesignId}
              className="text-xs font-semibold"
            >
              {loading ? 'Creating...' : 'Dispatch to Production'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
