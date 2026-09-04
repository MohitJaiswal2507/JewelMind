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
      <Card className="lg:col-span-2 bg-[#0b0f19] border-slate-800 shadow-xl flex flex-col justify-between overflow-hidden">
        <CardHeader className="p-6 pb-4 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-purple-400">
                <Factory className="w-5 h-5" />
                <CardTitle className="text-base sm:text-lg">
                  Workshop Operations & CP-SAT Schedule
                </CardTitle>
              </div>
              <CardDescription className="text-xs">
                Resource allocation & Google OR-Tools constraint optimization status
              </CardDescription>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onNavigateToProduction('optimization')}
              className="text-xs font-semibold"
            >
              <span>View Full Optimizer</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          {/* Workshop Resources Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1">
                <Users className="w-3 h-3 text-emerald-400" /> Artisans
              </div>
              <div className="text-lg font-bold text-white">
                {kpis.available_workers} <span className="text-xs text-slate-500 font-normal">/ {kpis.total_workers}</span>
              </div>
              <div className="text-[10px] text-emerald-400 font-mono">
                {kpis.total_worker_capacity_hours}h daily cap
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1">
                <Cpu className="w-3 h-3 text-sky-400" /> Machinery
              </div>
              <div className="text-lg font-bold text-white">
                {kpis.available_machines} <span className="text-xs text-slate-500 font-normal">/ {kpis.total_machines}</span>
              </div>
              <div className="text-[10px] text-sky-400 font-mono">
                {kpis.total_machine_capacity_hours}h daily cap
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1">
                <Factory className="w-3 h-3 text-amber-400" /> Pending Batches
              </div>
              <div className="text-lg font-bold text-amber-400">{kpis.pending_orders}</div>
              <div className="text-[10px] text-slate-400 font-mono">
                {kpis.in_progress_orders} in progress
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
              <div className="text-[11px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3 text-rose-400" /> Overdue Orders
              </div>
              <div className={`text-lg font-bold ${kpis.overdue_orders > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {kpis.overdue_orders}
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                {kpis.on_time_delivery_rate}% on-time
              </div>
            </div>
          </div>

          {/* Active Schedule Showcase */}
          {latestSchedule ? (
            <div className="p-4 rounded-xl bg-gradient-to-br from-purple-950/20 via-slate-950/60 to-slate-900/60 border border-purple-500/30 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-bold text-white">{latestSchedule.name}</span>
                  <Badge variant="gold" className="text-[10px]">
                    {latestSchedule.solver_status}
                  </Badge>
                </div>
                <span className="text-[11px] text-slate-400 font-mono">
                  Horizon: {latestSchedule.horizon_days} Days ({latestSchedule.makespan_hours} hrs makespan)
                </span>
              </div>

              {/* Progress bars */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div className="space-y-1">
                  <div className="flex justify-between text-[11px] text-slate-300">
                    <span>Artisan Utilization</span>
                    <span className="font-mono font-bold text-purple-400">
                      {latestSchedule.worker_utilization_pct}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-indigo-400 h-2 rounded-full"
                      style={{ width: `${Math.min(100, latestSchedule.worker_utilization_pct)}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-[11px] text-slate-300">
                    <span>Machine Utilization</span>
                    <span className="font-mono font-bold text-sky-400">
                      {latestSchedule.machine_utilization_pct}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-sky-500 to-cyan-400 h-2 rounded-full"
                      style={{ width: `${Math.min(100, latestSchedule.machine_utilization_pct)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800/80">
                <span>Scheduled Orders: {latestSchedule.total_orders_scheduled}</span>
                <span>Solver Runtime: {latestSchedule.runtime_seconds}s</span>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-slate-950/40 border border-dashed border-slate-800 text-center space-y-3">
              <Sliders className="w-6 h-6 text-slate-600 mx-auto" />
              <div className="space-y-0.5">
                <div className="text-xs font-bold text-white">No Production Schedule Generated</div>
                <p className="text-[11px] text-slate-400 max-w-md mx-auto">
                  Run Google OR-Tools CP-SAT constraint solver to optimize task precedence, artisan workbenches, and machine availability.
                </p>
              </div>
              <Button
                variant="gold"
                size="sm"
                onClick={() => onNavigateToProduction('optimization')}
                className="text-xs font-bold"
              >
                <Play className="w-3 h-3 mr-1.5" />
                Run Optimization Solver
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Right Col: Urgent Deadlines Tracker */}
      <Card className="bg-[#0b0f19] border-slate-800 shadow-xl flex flex-col justify-between overflow-hidden">
        <CardHeader className="p-6 pb-4 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-amber-400">
                <Calendar className="w-5 h-5" />
                <CardTitle className="text-base">Upcoming Deadlines</CardTitle>
              </div>
              <CardDescription className="text-xs">
                Urgent & pending customer orders
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

        <CardContent className="p-6 flex-1 flex flex-col justify-between">
          {deadlines.length === 0 ? (
            <div className="py-8 text-center space-y-2 text-slate-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/40 mx-auto" />
              <p className="text-slate-400 font-medium">All orders completed!</p>
              <p className="text-[11px]">No pending deadlines on the horizon.</p>
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
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                      order.is_overdue
                        ? 'bg-rose-500/10 border-rose-500/40 hover:bg-rose-500/20'
                        : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="text-xs font-bold text-white truncate">
                        {order.design_name || 'Jewellery Batch'}
                      </div>
                      <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                        <span className="capitalize">{order.priority}</span>
                        <span>•</span>
                        <span>Qty: {order.quantity}</span>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <div
                        className={`text-xs font-bold font-mono ${
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

          <div className="pt-4 border-t border-slate-800/80 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigateToProduction('orders')}
              className="w-full text-xs font-semibold border-slate-800 hover:border-slate-700"
            >
              Manage Workshop Orders
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
