/**
 * Production Execution TypeScript Definitions (Phase J.1 Foundation)
 * Defines types for shop-floor operation execution tracking, state transitions, and timing.
 */

export type ExecutionStatus =
  | 'pending'
  | 'ready'
  | 'in_progress'
  | 'paused'
  | 'completed'
  | 'blocked';

export const EXECUTION_STATUSES: { value: ExecutionStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'Pending', color: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
  { value: 'ready', label: 'Ready to Start', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  { value: 'paused', label: 'Paused', color: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
  { value: 'completed', label: 'Completed', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { value: 'blocked', label: 'Blocked', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
];

export interface OperationExecution {
  id: string;
  user_id: string;
  production_order_id: string;
  production_step_id: string;
  scheduled_task_id: string | null;
  worker_id: string | null;
  machine_id: string | null;

  status: ExecutionStatus;

  // Planned timing
  planned_start_time: string | null;
  planned_end_time: string | null;
  planned_duration_hours: number | null;

  // Actual timing
  actual_start_time: string | null;
  actual_end_time: string | null;
  actual_duration_hours: number | null;
  pause_duration_hours: number;
  last_paused_at: string | null;
  completed_at: string | null;

  operator_notes: string | null;
  created_at: string;
  updated_at: string;

  // Contextual step/resource metadata
  step_number?: number | null;
  stage_name?: string | null;
  required_skill?: string | null;
  required_machine_type?: string | null;
  quality_checkpoint?: string | null;
  worker_name?: string | null;
  machine_name?: string | null;
}

export interface OperationExecutionTransitionRequest {
  target_status: ExecutionStatus;
  operator_notes?: string | null;
  worker_id?: string | null;
  machine_id?: string | null;
}

export interface OperationExecutionCreate {
  production_order_id: string;
  production_step_id: string;
  scheduled_task_id?: string | null;
  worker_id?: string | null;
  machine_id?: string | null;
  operator_notes?: string | null;
}

export interface OperationExecutionListResponse {
  order_id: string;
  total: number;
  items: OperationExecution[];
}
