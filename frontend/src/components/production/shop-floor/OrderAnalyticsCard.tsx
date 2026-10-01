import React from 'react';
import {
  Clock,
  Package,
  Layers,
  Calendar,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { Badge } from '../../ui/badge';
import { ProductionOrderAnalyticsResponse } from '../../../types/analytics';

interface OrderAnalyticsCardProps {
  analytics: ProductionOrderAnalyticsResponse | null;
  loading?: boolean;
}

export const OrderAnalyticsCard: React.FC<OrderAnalyticsCardProps> = ({
  analytics,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-5 backdrop-blur-md shadow-xl animate-pulse">
        <div className="h-4 w-40 bg-white/10 rounded mb-4" />
        <div className="h-28 bg-white/5 rounded" />
      </div>
    );
  }

  if (!analytics) return null;

  const { planned, actual, variance, operations, quality, rework, schedule } = analytics;

  const isTimeOver = variance.hours > 0;
  const timeVariancePctDisplay = variance.hours_percent !== null
    ? `${variance.hours_percent > 0 ? '+' : ''}${variance.hours_percent.toFixed(1)}%`
    : 'N/A';

  const formattedStart = schedule.actual_start
    ? new Date(schedule.actual_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : schedule.planned_start
    ? new Date(schedule.planned_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '--';

  const formattedEnd = schedule.actual_completion
    ? new Date(schedule.actual_completion).toLocaleDateString([], { month: 'short', day: 'numeric' })
    : schedule.deadline
    ? new Date(schedule.deadline).toLocaleDateString([], { month: 'short', day: 'numeric' })
    : '--';

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/95 p-5 backdrop-blur-md shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-amber-300" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Planned vs Actual Analytics
          </h2>
        </div>
        <span className="font-mono text-[11px] text-slate-400">
          Order #{analytics.order_id.slice(0, 8)}
        </span>
      </div>

      {/* 4 Analytics Grid Sections */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        {/* Section 1: Bench Hours & Variance */}
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Bench Labor Time
            </span>
            {variance.hours === 0 ? (
              <Badge variant="outline" className="text-[9px] py-0 px-1 font-mono">On Target</Badge>
            ) : isTimeOver ? (
              <Badge variant="destructive" className="text-[9px] py-0 px-1 font-mono flex items-center">
                <TrendingUp className="w-2.5 h-2.5 mr-0.5" />
                {timeVariancePctDisplay}
              </Badge>
            ) : (
              <Badge variant="success" className="text-[9px] py-0 px-1 font-mono flex items-center">
                <TrendingDown className="w-2.5 h-2.5 mr-0.5" />
                {timeVariancePctDisplay}
              </Badge>
            )}
          </div>

          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Planned Norm:</span>
              <span className="font-mono text-slate-200">{planned.hours.toFixed(2)}h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Actual Logged:</span>
              <span className="font-mono text-white font-bold">{actual.hours.toFixed(2)}h</span>
            </div>
            <div className="flex justify-between pt-1 border-t border-white/[0.04]">
              <span className="text-slate-400">Variance:</span>
              <span
                className={`font-mono font-bold ${
                  isTimeOver ? 'text-rose-400' : variance.hours < 0 ? 'text-emerald-400' : 'text-slate-300'
                }`}
              >
                {variance.hours > 0 ? `+${variance.hours.toFixed(2)}h` : `${variance.hours.toFixed(2)}h`}
              </span>
            </div>
          </div>
        </div>

        {/* Section 2: Material & Wastage */}
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Material Variance
            </span>
            <Package className="w-3.5 h-3.5 text-amber-300/80" />
          </div>

          {variance.materials.length === 0 ? (
            <p className="text-[11px] text-slate-500 italic mt-2">No consumption recorded</p>
          ) : (
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Planned:</span>
                <span className="font-mono text-slate-200">
                  {variance.materials[0].planned_quantity.toFixed(2)} {variance.materials[0].unit}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Actual:</span>
                <span className="font-mono text-white font-bold">
                  {variance.materials[0].actual_quantity.toFixed(2)} {variance.materials[0].unit}
                </span>
              </div>
              <div className="flex justify-between pt-1 border-t border-white/[0.04]">
                <span className="text-slate-400">Wastage / Scrap:</span>
                <span className="font-mono text-rose-300 font-medium">
                  {variance.materials[0].wastage_quantity.toFixed(2)} {variance.materials[0].unit}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Section 3: Operations & Quality */}
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Operations & QC
            </span>
            <Layers className="w-3.5 h-3.5 text-purple-300" />
          </div>

          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Routing Progress:</span>
              <span className="font-mono text-white font-bold">
                {operations.completed}/{operations.total} ({operations.completion_rate_percent}%)
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">QC Verdicts:</span>
              <span className="font-mono text-emerald-300">
                {quality.passed} PASS{' '}
                <span className="text-slate-500">/ {quality.failed} FAIL</span>
              </span>
            </div>
            <div className="flex justify-between pt-1 border-t border-white/[0.04]">
              <span className="text-slate-400">Rework Count:</span>
              <span className="font-mono text-amber-300 font-bold">
                {rework.count} attempts ({rework.rate_percent}%)
              </span>
            </div>
          </div>
        </div>

        {/* Section 4: Schedule Milestones */}
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Schedule Milestones
            </span>
            <Calendar className="w-3.5 h-3.5 text-blue-300" />
          </div>

          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Start Time:</span>
              <span className="font-mono text-slate-200">{formattedStart}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Target Due:</span>
              <span className="font-mono text-slate-200">{formattedEnd}</span>
            </div>
            <div className="flex justify-between pt-1 border-t border-white/[0.04]">
              <span className="text-slate-400">Schedule Status:</span>
              <span className="font-mono font-medium">
                {schedule.is_overdue ? (
                  <span className="text-rose-400 font-bold">OVERDUE</span>
                ) : schedule.schedule_variance_hours !== null ? (
                  schedule.schedule_variance_hours > 0 ? (
                    <span className="text-rose-400">+{schedule.schedule_variance_hours}h delay</span>
                  ) : (
                    <span className="text-emerald-400">{Math.abs(schedule.schedule_variance_hours)}h early</span>
                  )
                ) : (
                  <span className="text-slate-300">On Track</span>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
