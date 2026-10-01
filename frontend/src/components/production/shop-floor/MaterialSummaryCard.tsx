import React from 'react';
import { Package } from 'lucide-react';
import { OrderMaterialSummaryResponse } from '../../../types/execution';

interface MaterialSummaryCardProps {
  summary: OrderMaterialSummaryResponse | null;
  loading?: boolean;
}

export const MaterialSummaryCard: React.FC<MaterialSummaryCardProps> = ({
  summary,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-5 backdrop-blur-md shadow-xl animate-pulse">
        <div className="h-4 w-32 bg-white/10 rounded mb-4" />
        <div className="h-20 bg-white/5 rounded" />
      </div>
    );
  }

  if (!summary || summary.items.length === 0) {
    return (
      <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-5 backdrop-blur-md shadow-xl text-center">
        <Package className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <h3 className="text-xs font-semibold text-slate-300">No Material Logged Yet</h3>
        <p className="text-[11px] text-slate-500 mt-0.5">
          Artisans log gold grain, alloys, and gems as operations progress.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-5 backdrop-blur-md shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
        <div className="flex items-center space-x-2">
          <Package className="w-4 h-4 text-amber-300" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Material Consumption & Wastage
          </h2>
        </div>
        <span className="text-[10px] font-mono text-amber-300/80 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">
          {summary.items.length} materials
        </span>
      </div>

      <div className="space-y-3">
        {summary.items.map((item, idx) => {
          const wastagePct = item.actual_quantity > 0
            ? ((item.wastage_quantity / item.actual_quantity) * 100).toFixed(1)
            : '0.0';

          return (
            <div
              key={idx}
              className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-white">{item.material_name}</h4>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">
                    Type: {item.material_type}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-amber-200 font-mono">
                    {item.actual_quantity.toFixed(2)} {item.unit}
                  </span>
                  <span className="text-[10px] text-slate-500 block">Actual Net</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-1 border-t border-white/[0.04] text-[11px]">
                <div>
                  <span className="text-slate-500 block text-[9px] uppercase">Planned</span>
                  <span className="font-mono text-slate-300">
                    {item.planned_quantity ? `${item.planned_quantity.toFixed(2)} ${item.unit}` : '--'}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block text-[9px] uppercase">Wastage / Dust</span>
                  <span className="font-mono text-rose-300 font-medium">
                    {item.wastage_quantity.toFixed(2)} {item.unit} ({wastagePct}%)
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block text-[9px] uppercase">Gross Used</span>
                  <span className="font-mono text-amber-300/90 font-medium">
                    {(item.actual_quantity + item.wastage_quantity).toFixed(2)} {item.unit}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
