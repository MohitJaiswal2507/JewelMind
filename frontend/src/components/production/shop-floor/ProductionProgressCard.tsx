import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { OrderQualitySummaryResponse } from '../../../types/execution';

interface ProductionProgressCardProps {
  totalOperations: number;
  completedOperations: number;
  qualitySummary: OrderQualitySummaryResponse | null;
  onCompleteOrder?: () => void;
  canCompleteOrder?: boolean;
  completingOrder?: boolean;
}

export const ProductionProgressCard: React.FC<ProductionProgressCardProps> = ({
  totalOperations,
  completedOperations,
  qualitySummary,
  onCompleteOrder,
  canCompleteOrder = false,
  completingOrder = false,
}) => {
  const percent = totalOperations > 0
    ? Math.round((completedOperations / totalOperations) * 100)
    : 0;

  const passed = qualitySummary?.passed ?? 0;
  const failed = qualitySummary?.failed ?? 0;
  const rework = qualitySummary?.rework ?? 0;
  const pendingQc = qualitySummary?.pending_quality_checks ?? 0;
  const gatePassed = qualitySummary?.quality_gate_passed ?? false;

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-5 backdrop-blur-md shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-amber-300" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Workstation Progress & Quality Gate
          </h2>
        </div>
        <span className="font-mono text-xs font-bold text-amber-300">
          {percent}% Complete
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-white/[0.05] h-2.5 rounded-full overflow-hidden border border-white/[0.05]">
        <div
          className="bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-300 h-full rounded-full transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
        <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Passed QC</span>
          <span className="font-mono text-base font-bold text-emerald-400">{passed}</span>
        </div>

        <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Rework</span>
          <span className="font-mono text-base font-bold text-amber-400">{rework}</span>
        </div>

        <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Failed</span>
          <span className="font-mono text-base font-bold text-rose-400">{failed}</span>
        </div>

        <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Pending QC</span>
          <span className="font-mono text-base font-bold text-slate-300">{pendingQc}</span>
        </div>
      </div>

      {/* Quality Gate Status & Final Order Completion */}
      <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          {gatePassed ? (
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
          )}
          <div>
            <span className="text-xs font-semibold text-white block">
              {gatePassed ? 'Production Quality Gate Passed' : 'Quality Gate Incomplete'}
            </span>
            <p className="text-[11px] text-slate-400 font-light">
              {gatePassed
                ? 'All routing operations verified with passing quality inspection.'
                : 'All operations must be completed and hold PASS quality status before order completion.'}
            </p>
          </div>
        </div>

        {onCompleteOrder && (
          <Button
            variant="gold"
            size="sm"
            disabled={!canCompleteOrder || completingOrder}
            onClick={onCompleteOrder}
            className="text-xs font-bold shrink-0 shadow-lg shadow-amber-500/10"
          >
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
            {completingOrder ? 'Finalizing...' : 'Finalize Production Order'}
          </Button>
        )}
      </div>
    </div>
  );
};
