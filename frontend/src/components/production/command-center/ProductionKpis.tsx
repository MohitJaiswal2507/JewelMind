import React from 'react';
import {
  Layers,
  ShieldAlert,
  Clock,
  IndianRupee,
  Users,
  Repeat,
} from 'lucide-react';
import { Card, CardContent } from '../../ui/card';
import { ProductionSummary } from '../../../types/production';

interface ProductionKpisProps {
  summary: ProductionSummary | null;
  awaitingQcCount: number;
  delayedCount: number;
  totalMaterialValue: number;
  reworkCount: number;
  reworkRatePercent: number | null;
  loading?: boolean;
}

export const ProductionKpis: React.FC<ProductionKpisProps> = ({
  summary,
  awaitingQcCount,
  delayedCount,
  totalMaterialValue,
  reworkCount,
  reworkRatePercent,
  loading = false,
}) => {
  const activeOrders = summary ? summary.in_progress_orders + summary.pending_orders : 0;
  const workersActive = summary ? `${summary.available_workers}/${summary.total_workers}` : '—';
  const workerHours = summary ? `${summary.total_worker_capacity_hours}h` : '—';

  const formattedMaterialValue = totalMaterialValue > 0
    ? totalMaterialValue >= 100000
      ? `₹${(totalMaterialValue / 100000).toFixed(2)}L`
      : `₹${totalMaterialValue.toLocaleString('en-IN')}`
    : '—';

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
      {/* 1. Active Production */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07] hover:border-amber-400/30 transition-all duration-200">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Active Orders</span>
            <div className="p-1.5 rounded-lg bg-amber-400/10 text-amber-300">
              <Layers className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-serif font-bold text-white tracking-tight">
              {loading ? '...' : activeOrders}
            </div>
            <div className="text-[11px] text-slate-400 font-light mt-0.5 flex items-center gap-1.5">
              <span className="text-cyan-300">{summary?.in_progress_orders ?? 0} in progress</span>
              <span className="text-slate-600">•</span>
              <span>{summary?.pending_orders ?? 0} pending</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Awaiting QC */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07] hover:border-cyan-400/30 transition-all duration-200">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Awaiting QC</span>
            <div className="p-1.5 rounded-lg bg-cyan-400/10 text-cyan-300">
              <ShieldAlert className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-serif font-bold text-white tracking-tight">
              {loading ? '...' : awaitingQcCount}
            </div>
            <div className="text-[11px] text-slate-400 font-light mt-0.5">
              {awaitingQcCount > 0 ? (
                <span className="text-cyan-300 font-medium">Inspection required</span>
              ) : (
                <span className="text-emerald-400 font-medium">All checkpoints clear</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3. Delayed Orders */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07] hover:border-rose-400/30 transition-all duration-200">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Delayed</span>
            <div className="p-1.5 rounded-lg bg-rose-400/10 text-rose-300">
              <Clock className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-serif font-bold text-white tracking-tight">
              {loading ? '...' : delayedCount}
            </div>
            <div className="text-[11px] text-slate-400 font-light mt-0.5">
              {delayedCount > 0 ? (
                <span className="text-rose-400 font-medium">Behind deadline</span>
              ) : (
                <span className="text-emerald-400 font-medium">Schedule on track</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 4. Material Value in Production (₹) */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07] hover:border-emerald-400/30 transition-all duration-200">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Material Value</span>
            <div className="p-1.5 rounded-lg bg-emerald-400/10 text-emerald-300">
              <IndianRupee className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-serif font-bold text-emerald-300 tracking-tight">
              {loading ? '...' : formattedMaterialValue}
            </div>
            <div className="text-[11px] text-slate-400 font-light mt-0.5 truncate" title="Calculated from BOM / Consumption weights at IBJA bullion rate">
              Active metals in flow
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 5. Karigar Workshop Capacity */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07] hover:border-blue-400/30 transition-all duration-200">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Karigars Active</span>
            <div className="p-1.5 rounded-lg bg-blue-400/10 text-blue-300">
              <Users className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-serif font-bold text-white tracking-tight">
              {loading ? '...' : workersActive}
            </div>
            <div className="text-[11px] text-slate-400 font-light mt-0.5">
              <span className="text-blue-300 font-medium">{workerHours}</span> daily capacity
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 6. Rework Rate */}
      <Card className="bg-[#0E111A]/95 border-white/[0.07] hover:border-amber-400/30 transition-all duration-200">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">Rework Rate</span>
            <div className="p-1.5 rounded-lg bg-purple-400/10 text-purple-300">
              <Repeat className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-serif font-bold text-white tracking-tight">
              {loading ? '...' : reworkRatePercent !== null ? `${reworkRatePercent.toFixed(1)}%` : reworkCount > 0 ? `${reworkCount} loops` : '0%'}
            </div>
            <div className="text-[11px] text-slate-400 font-light mt-0.5">
              {reworkCount > 0 ? (
                <span className="text-amber-400 font-medium">{reworkCount} active rework loops</span>
              ) : (
                <span className="text-emerald-400 font-medium">Optimal first-pass yield</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
