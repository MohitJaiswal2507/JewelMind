import React from 'react';
import {
  Factory,
  Users,
  Cpu,
  Clock,
  CheckCircle2,
  Sliders,
  Calendar,
  ArrowRight,
  Play,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  DashboardKpis,
  DashboardDeadlineOrder,
  DashboardLatestSchedule,
} from '../../types/dashboard';

interface DashboardProductionOverviewProps {
  kpis: DashboardKpis;
  deadlines: DashboardDeadlineOrder[];
  latestSchedule: DashboardLatestSchedule | null;
  onNavigateToProduction: (tab?: string) => void;
  onSelectDesign: (designId: string) => void;
}

export const DashboardProductionOverview: React.FC<DashboardProductionOverviewProps> = ({
  kpis,
  deadlines,
  latestSchedule,
  onNavigateToProduction,
  onSelectDesign,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left 2 Cols: Workshop Capacity & CP-SAT Schedule Highlight */}
      <Card className="lg:col-span-2 bg-[#0E111A]/90 border-white/[0.07] shadow-2xl flex flex-col justify-between overflow-hidden">
        <CardHeader className="p-6 sm:p-7 pb-4 border-b border-white/[0.06] bg-[#0A0C12]/50">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-300">
                <Factory className="w-5 h-5" />
                <CardTitle className="text-lg font-serif font-medium">
                  Workshop Operations & CP-SAT Schedule
                </CardTitle>
              </div>
              <CardDescription className="text-xs text-slate-400 font-light">
                Resource allocation & Google OR-Tools constraint optimization status
              </CardDescription>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onNavigateToProduction('optimization')}
              className="text-xs font-medium"
            >
              <span>View Full Optimizer</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-6 sm:p-7 space-y-6">
          {/* Workshop Resources Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5 font-light">
                <Users className="w-3.5 h-3.5 text-emerald-400" /> Artisans
              </div>
              <div className="font-serif text-xl font-medium text-white">
                {kpis.available_workers} <span className="text-xs text-slate-500 font-sans font-normal">/ {kpis.total_workers}</span>
              </div>
              <div className="text-[10px] text-emerald-400 font-mono">
                {kpis.total_worker_capacity_hours}h daily cap
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5 font-light">
                <Cpu className="w-3.5 h-3.5 text-sky-400" /> Machinery
              </div>
              <div className="font-serif text-xl font-medium text-white">
                {kpis.available_machines} <span className="text-xs text-slate-500 font-sans font-normal">/ {kpis.total_machines}</span>
              </div>
              <div className="text-[10px] text-sky-400 font-mono">
                {kpis.total_machine_capacity_hours}h daily cap
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5 font-light">
                <Factory className="w-3.5 h-3.5 text-amber-300" /> Pending Batches
              </div>
              <div className="font-serif text-xl font-medium text-amber-300">{kpis.pending_orders}</div>
              <div className="text-[10px] text-slate-400 font-mono">
                {kpis.in_progress_orders} in progress
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#080A10] border border-white/5 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5 font-light">
                <Clock className="w-3.5 h-3.5 text-rose-400" /> Overdue Orders
              </div>
              <div className={`font-serif text-xl font-medium ${kpis.overdue_orders > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {kpis.overdue_orders}
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                {kpis.on_time_delivery_rate}% on-time
              </div>
            </div>
          </div>

          {/* Active Schedule Showcase */}
          {latestSchedule ? (
            <div className="p-4.5 rounded-xl bg-[#080A10] border border-amber-400/20 space-y-3.5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-semibold text-white">{latestSchedule.name}</span>
                  <Badge variant="gold" className="text-[9px]">
                    {latestSchedule.solver_status}
                  </Badge>
                </div>
                <span className="text-[11px] text-slate-400 font-mono font-light">
                  Horizon: {latestSchedule.horizon_days} Days ({latestSchedule.makespan_hours}h makespan)
                </span>
              </div>

              {/* Progress bars */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[11px] text-slate-300">
                    <span className="font-light">Artisan Bench Utilization</span>
                    <span className="font-mono font-semibold text-amber-300">
                      {latestSchedule.worker_utilization_pct}%
                    </span>
                  </div>
                  <div className="w-full bg-[#121622] rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-amber-500 to-amber-300 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, latestSchedule.worker_utilization_pct)}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-[11px] text-slate-300">
                    <span className="font-light">Machinery Utilization</span>
                    <span className="font-mono font-semibold text-slate-300">
                      {latestSchedule.machine_utilization_pct}%
                    </span>
                  </div>
                  <div className="w-full bg-[#121622] rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-slate-400 to-slate-200 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, latestSchedule.machine_utilization_pct)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-white/5">
                <span>Scheduled Orders: {latestSchedule.total_orders_scheduled}</span>
                <span>Solver Runtime: {latestSchedule.runtime_seconds}s</span>
              </div>
            </div>
          ) : (
            <div className="p-5 rounded-xl bg-[#080A10] border border-dashed border-white/10 text-center space-y-3">
              <Sliders className="w-6 h-6 text-slate-600 mx-auto" />
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-white">No Production Schedule Generated</div>
                <p className="text-[11px] text-slate-400 font-light max-w-md mx-auto">
                  Run Google OR-Tools CP-SAT constraint solver to optimize task precedence, artisan workbenches, and machine availability.
                </p>
              </div>
              <Button
                variant="gold"
                size="sm"
                onClick={() => onNavigateToProduction('optimization')}
                className="text-xs font-semibold"
              >
                <Play className="w-3 h-3 mr-1.5" />
                Run Optimization Solver
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Right Col: Urgent Deadlines Tracker */}
      <Card className="bg-[#0E111A]/90 border-white/[0.07] shadow-2xl flex flex-col justify-between overflow-hidden">
        <CardHeader className="p-6 sm:p-7 pb-4 border-b border-white/[0.06] bg-[#0A0C12]/50">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-300">
                <Calendar className="w-5 h-5" />
                <CardTitle className="text-base font-serif font-medium">Upcoming Deadlines</CardTitle>
              </div>
              <CardDescription className="text-xs text-slate-400 font-light">
                Priority client commissions
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigateToProduction('orders')}
              className="text-xs text-slate-400 hover:text-white"
            >
              All Orders
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-6 sm:p-7 flex-1 flex flex-col justify-between">
          {deadlines.length === 0 ? (
            <div className="py-8 text-center space-y-2 text-slate-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/40 mx-auto" />
              <p className="text-slate-400 font-medium">All commissions fulfilled</p>
              <p className="text-[11px] font-light">No pending deadlines on the horizon.</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {deadlines.map((order) => {
                const deadlineDate = new Date(order.deadline).toLocaleDateString([], {
                  month: 'short',
                  day: 'numeric',
                });
                return (
                  <div
                    key={order.id}
                    onClick={() => onSelectDesign(order.design_id)}
                    className={`p-3 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between gap-3 ${
                      order.is_overdue
                        ? 'bg-rose-500/10 border-rose-500/30 hover:bg-rose-500/20'
                        : 'bg-[#080A10] border-white/5 hover:border-white/15'
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="text-xs font-semibold text-white truncate">
                        {order.design_name || 'Jewellery Commission'}
                      </div>
                      <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-light">
                        <span className="capitalize">{order.priority}</span>
                        <span>•</span>
                        <span>Qty: {order.quantity}</span>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <div
                        className={`text-xs font-mono font-semibold ${
                          order.is_overdue ? 'text-rose-400' : 'text-slate-300'
                        }`}
                      >
                        {deadlineDate}
                      </div>
                      <span
                        className={`text-[9px] font-semibold uppercase ${
                          order.is_overdue ? 'text-rose-400' : 'text-slate-500'
                        }`}
                      >
                        {order.is_overdue ? 'OVERDUE' : order.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="pt-4 border-t border-white/5 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigateToProduction('orders')}
              className="w-full text-xs font-semibold border-white/10 hover:border-white/20"
            >
              Manage Workshop Orders
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
