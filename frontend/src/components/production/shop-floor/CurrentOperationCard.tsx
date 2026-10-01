import React from 'react';
import {
  Play,
  Pause,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  Cpu,
  ShieldCheck,
  RotateCcw,
  PackagePlus,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { ExecutionTimer } from './ExecutionTimer';
import { OperationExecution } from '../../../types/execution';

interface CurrentOperationCardProps {
  execution: OperationExecution;
  onAssignWorker: () => void;
  onAssignMachine: () => void;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onComplete: () => void;
  onBlock: () => void;
  onMakeReady: () => void;
  onOpenQc: () => void;
  onCreateRework: () => void;
  onOpenMaterialModal: () => void;
  actionLoading?: boolean;
}

export const CurrentOperationCard: React.FC<CurrentOperationCardProps> = ({
  execution,
  onAssignWorker,
  onAssignMachine,
  onStart,
  onPause,
  onResume,
  onComplete,
  onBlock,
  onMakeReady,
  onOpenQc,
  onCreateRework,
  onOpenMaterialModal,
  actionLoading = false,
}) => {
  const isRework = execution.execution_type === 'rework' || (execution.attempt_number ?? 1) > 1;
  const isTerminal = execution.is_terminal;

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0E111A]/95 p-6 backdrop-blur-md shadow-2xl space-y-6">
      {/* Top Banner: Operation Identification */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs font-bold text-amber-300 uppercase tracking-widest">
              Operation {execution.step_number ?? '-'}
            </span>
            <span className="text-white/20">&bull;</span>
            <Badge
              variant="outline"
              className={`text-xs uppercase font-mono font-bold ${
                execution.status === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : execution.status === 'in_progress'
                  ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                  : execution.status === 'paused'
                  ? 'bg-orange-500/15 text-orange-300 border-orange-500/30'
                  : execution.status === 'ready'
                  ? 'bg-blue-500/15 text-blue-300 border-blue-500/30'
                  : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
              }`}
            >
              {execution.status.replace('_', ' ')}
            </Badge>
            {isRework && (
              <Badge variant="destructive" className="font-mono text-[10px] bg-purple-500/20 text-purple-300 border-purple-500/30">
                Rework Attempt {execution.attempt_number || 2}
              </Badge>
            )}
            {isTerminal && (
              <Badge variant="outline" className="text-[10px] text-amber-200 border-amber-400/30">
                Final Step
              </Badge>
            )}
          </div>

          <h2 className="text-xl sm:text-2xl font-serif font-bold text-white mt-1">
            {execution.stage_name || `Manufacturing Step ${execution.step_number || ''}`}
          </h2>
        </div>

        {/* Action Button: Log Material */}
        {(execution.status === 'in_progress' || execution.status === 'completed') && (
          <Button
            variant="atelier"
            size="sm"
            onClick={onOpenMaterialModal}
            className="self-start sm:self-center text-xs font-medium"
          >
            <PackagePlus className="w-3.5 h-3.5 mr-1.5 text-amber-300" />
            Log Material & Scrap
          </Button>
        )}
      </div>

      {/* Timer Section */}
      <ExecutionTimer
        status={execution.status}
        actualStartTime={execution.actual_start_time}
        pauseDurationHours={execution.pause_duration_hours}
        lastPausedAt={execution.last_paused_at}
        actualDurationHours={execution.actual_duration_hours}
        plannedDurationHours={execution.planned_duration_hours}
      />

      {/* Resource Allocation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Worker Allocation Card */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                Assigned Artisan
              </span>
              <span className="text-sm font-semibold text-white">
                {execution.worker_name || 'Unassigned'}
              </span>
              <span className="text-xs text-slate-400 block">
                Required: <strong className="text-slate-300">{execution.required_skill || 'Goldsmithing'}</strong>
              </span>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            disabled={execution.status === 'completed' || actionLoading}
            onClick={onAssignWorker}
            className="text-xs border-white/10 hover:border-amber-400/40"
          >
            {execution.worker_id ? 'Reassign' : 'Assign'}
          </Button>
        </div>

        {/* Machine Allocation Card */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                Workshop Machine
              </span>
              <span className="text-sm font-semibold text-white">
                {execution.machine_name || 'Unassigned'}
              </span>
              <span className="text-xs text-slate-400 block">
                Required: <strong className="text-slate-300">{execution.required_machine_type || 'Manual Workbench'}</strong>
              </span>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            disabled={execution.status === 'completed' || actionLoading}
            onClick={onAssignMachine}
            className="text-xs border-white/10 hover:border-amber-400/40"
          >
            {execution.machine_id ? 'Reassign' : 'Assign'}
          </Button>
        </div>
      </div>

      {/* QC Status & Inspection Section */}
      <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            {execution.latest_qc_result === 'FAIL' ? (
              <ShieldAlert className="w-5 h-5 text-rose-400" />
            ) : execution.latest_qc_result === 'REWORK' ? (
              <RotateCcw className="w-5 h-5 text-amber-400" />
            ) : (
              <ShieldCheck className="w-5 h-5" />
            )}
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
              Quality Inspection
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-white">
                {execution.latest_qc_result ? `Verdict: ${execution.latest_qc_result}` : 'Not Yet Inspected'}
              </span>
              {execution.latest_defect_severity && execution.latest_defect_severity !== 'NONE' && (
                <Badge variant="destructive" className="text-[9px] py-0 px-1 font-mono">
                  {execution.latest_defect_severity} Defect
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {execution.status === 'completed' && (
            <Button
              variant="atelier"
              size="sm"
              onClick={onOpenQc}
              className="text-xs font-semibold"
            >
              <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-amber-300" />
              {execution.latest_qc_result ? 'Re-inspect QC' : 'Perform QC'}
            </Button>
          )}

          {execution.latest_qc_result === 'REWORK' && (
            <Button
              variant="gold"
              size="sm"
              onClick={onCreateRework}
              disabled={actionLoading}
              className="text-xs font-bold"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              Authorize Rework Attempt
            </Button>
          )}
        </div>
      </div>

      {/* Primary Workstation Action Bar */}
      <div className="pt-2 flex flex-wrap items-center gap-3">
        {execution.status === 'ready' && (
          <Button
            variant="gold"
            size="lg"
            disabled={actionLoading}
            onClick={onStart}
            className="flex-1 text-sm font-bold shadow-lg shadow-amber-500/10"
          >
            <Play className="w-4 h-4 mr-2 fill-slate-950" />
            Start Operation
          </Button>
        )}

        {execution.status === 'in_progress' && (
          <>
            <Button
              variant="secondary"
              size="lg"
              disabled={actionLoading}
              onClick={onPause}
              className="flex-1 text-xs font-semibold"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause Work
            </Button>

            <Button
              variant="gold"
              size="lg"
              disabled={actionLoading}
              onClick={onComplete}
              className="flex-1 text-sm font-bold shadow-lg shadow-amber-500/10"
            >
              <CheckCircle2 className="w-4 h-4 mr-2 text-slate-950" />
              Complete Operation
            </Button>

            <Button
              variant="destructive"
              size="sm"
              disabled={actionLoading}
              onClick={onBlock}
              className="text-xs"
            >
              <AlertTriangle className="w-3.5 h-3.5 mr-1" />
              Block
            </Button>
          </>
        )}

        {execution.status === 'paused' && (
          <>
            <Button
              variant="gold"
              size="lg"
              disabled={actionLoading}
              onClick={onResume}
              className="flex-1 text-sm font-bold"
            >
              <Play className="w-4 h-4 mr-2 fill-slate-950" />
              Resume Work
            </Button>

            <Button
              variant="destructive"
              size="sm"
              disabled={actionLoading}
              onClick={onBlock}
              className="text-xs"
            >
              <AlertTriangle className="w-3.5 h-3.5 mr-1" />
              Block
            </Button>
          </>
        )}

        {execution.status === 'blocked' && (
          <Button
            variant="atelier"
            size="lg"
            disabled={actionLoading}
            onClick={onMakeReady}
            className="flex-1 text-xs font-semibold"
          >
            <ArrowRight className="w-4 h-4 mr-2 text-amber-300" />
            Clear Block / Make Ready
          </Button>
        )}

        {execution.status === 'pending' && (
          <div className="w-full p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] text-center text-xs text-slate-400">
            Awaiting completion of upstream routing operations before start authorization.
          </div>
        )}
      </div>
    </div>
  );
};
