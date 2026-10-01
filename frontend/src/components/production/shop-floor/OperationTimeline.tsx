import React from 'react';
import {
  CheckCircle2,
  Clock,
  Play,
  Pause,
  AlertCircle,
  ShieldCheck,
  ShieldAlert,
  RotateCcw,
} from 'lucide-react';
import { Badge } from '../../ui/badge';
import { OperationExecution } from '../../../types/execution';

interface OperationTimelineProps {
  executions: OperationExecution[];
  currentExecutionId: string | null;
  onSelectExecution: (execution: OperationExecution) => void;
}

export const OperationTimeline: React.FC<OperationTimelineProps> = ({
  executions,
  currentExecutionId,
  onSelectExecution,
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'in_progress':
        return <Play className="w-4 h-4 text-amber-400 fill-amber-400 animate-pulse" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-orange-400" />;
      case 'ready':
        return <Clock className="w-4 h-4 text-blue-400" />;
      case 'blocked':
        return <AlertCircle className="w-4 h-4 text-rose-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-600" />;
    }
  };

  const getQcBadge = (execution: OperationExecution) => {
    if (!execution.latest_qc_result) return null;
    switch (execution.latest_qc_result) {
      case 'PASS':
        return (
          <span className="inline-flex items-center text-[10px] text-emerald-300 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
            <ShieldCheck className="w-3 h-3 mr-1" />
            PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center text-[10px] text-rose-300 font-semibold bg-rose-500/10 border border-rose-500/20 px-1.5 py-0.5 rounded">
            <ShieldAlert className="w-3 h-3 mr-1" />
            FAIL
          </span>
        );
      case 'REWORK':
        return (
          <span className="inline-flex items-center text-[10px] text-amber-300 font-semibold bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">
            <RotateCcw className="w-3 h-3 mr-1" />
            REWORK
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/90 p-5 backdrop-blur-md shadow-xl">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Routing Sequence ({executions.length})
        </h2>
        <span className="text-[11px] text-slate-500">Tap step to inspect</span>
      </div>

      <div className="space-y-2">
        {executions.map((exec) => {
          const isSelected = exec.id === currentExecutionId;
          const isRework = exec.execution_type === 'rework' || (exec.attempt_number ?? 1) > 1;

          return (
            <div
              key={exec.id}
              onClick={() => onSelectExecution(exec)}
              className={`flex items-center justify-between p-3 rounded-xl border transition-all duration-200 cursor-pointer select-none ${
                isSelected
                  ? 'bg-amber-400/10 border-amber-400/40 shadow-lg shadow-amber-400/5'
                  : 'bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.04] hover:border-white/10'
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
                    exec.status === 'completed'
                      ? 'bg-emerald-500/10 border-emerald-500/30'
                      : exec.status === 'in_progress'
                      ? 'bg-amber-400/15 border-amber-400/40'
                      : 'bg-white/[0.04] border-white/10'
                  }`}
                >
                  {getStatusIcon(exec.status)}
                </div>

                <div className="min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs text-amber-300 font-bold shrink-0">
                      Step {exec.step_number ?? '-'}
                    </span>
                    <h3 className="text-xs font-semibold text-white truncate">
                      {exec.stage_name || `Operation ${exec.step_number || ''}`}
                    </h3>
                    {isRework && (
                      <Badge
                        variant="outline"
                        className="text-[9px] py-0 px-1 bg-purple-500/15 text-purple-300 border-purple-500/30 font-mono"
                      >
                        Rework #{exec.attempt_number || 2}
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5 truncate">
                    <span>{exec.worker_name || 'Unassigned Artisan'}</span>
                    <span>&bull;</span>
                    <span>{exec.machine_name || 'No Machine'}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 shrink-0 ml-2">
                {getQcBadge(exec)}
                <span
                  className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${
                    exec.status === 'completed'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : exec.status === 'in_progress'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      : exec.status === 'ready'
                      ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                      : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                  }`}
                >
                  {exec.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
