import React, { useState } from 'react';
import { X, IndianRupee, Check, RotateCcw } from 'lucide-react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { WorkshopRateConfig, DEFAULT_INDIAN_WORKSHOP_RATES } from '../../../types/materialValuation';

interface RateConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: WorkshopRateConfig;
  onSave: (newConfig: WorkshopRateConfig) => void;
}

export const RateConfigModal: React.FC<RateConfigModalProps> = ({
  isOpen,
  onClose,
  config,
  onSave,
}) => {
  const [rates, setRates] = useState<WorkshopRateConfig>({ ...config });

  if (!isOpen) return null;

  const handleReset = () => {
    setRates({ ...DEFAULT_INDIAN_WORKSHOP_RATES });
  };

  const handleSave = () => {
    onSave({
      ...rates,
      lastUpdated: new Date().toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' }),
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-[#0E111A] border border-white/[0.1] rounded-2xl shadow-2xl overflow-hidden space-y-5 p-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-400/10 text-amber-300 border border-amber-400/20">
              <IndianRupee className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-serif font-bold text-white">Atelier Bullion Benchmarks</h3>
              <p className="text-xs text-slate-400 font-light">Configure valuation rates for Indian fine jewellery production</p>
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
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">18K Gold Rate (₹/g)</label>
            <Input
              type="number"
              value={rates.gold18k}
              onChange={(e) => setRates({ ...rates, gold18k: parseFloat(e.target.value) || 0 })}
              className="bg-[#121624] border-white/[0.08] text-amber-300 font-mono h-9"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">22K Gold Rate (₹/g)</label>
            <Input
              type="number"
              value={rates.gold22k}
              onChange={(e) => setRates({ ...rates, gold22k: parseFloat(e.target.value) || 0 })}
              className="bg-[#121624] border-white/[0.08] text-amber-300 font-mono h-9"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">925 Sterling Silver (₹/g)</label>
            <Input
              type="number"
              value={rates.silver925}
              onChange={(e) => setRates({ ...rates, silver925: parseFloat(e.target.value) || 0 })}
              className="bg-[#121624] border-white/[0.08] text-slate-200 font-mono h-9"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">950 Platinum Rate (₹/g)</label>
            <Input
              type="number"
              value={rates.platinum950}
              onChange={(e) => setRates({ ...rates, platinum950: parseFloat(e.target.value) || 0 })}
              className="bg-[#121624] border-white/[0.08] text-slate-200 font-mono h-9"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">Karigar Rate (₹/hour)</label>
            <Input
              type="number"
              value={rates.standardKarigarHourlyRate}
              onChange={(e) => setRates({ ...rates, standardKarigarHourlyRate: parseFloat(e.target.value) || 0 })}
              className="bg-[#121624] border-white/[0.08] text-blue-300 font-mono h-9"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-medium">Target Margin Target (%)</label>
            <Input
              type="number"
              value={rates.standardRetailMarkupPercent}
              onChange={(e) => setRates({ ...rates, standardRetailMarkupPercent: parseFloat(e.target.value) || 0 })}
              className="bg-[#121624] border-white/[0.08] text-emerald-300 font-mono h-9"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-white/[0.08]">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="text-xs text-slate-400 hover:text-white"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1" />
            Reset Defaults
          </Button>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs border-[#1E2333] text-slate-300"
            >
              Cancel
            </Button>
            <Button
              variant="gold"
              size="sm"
              onClick={handleSave}
              className="text-xs font-semibold"
            >
              <Check className="w-3.5 h-3.5 mr-1" />
              Apply Rates
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
