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

  // Planned vs Actual execution resources (Phase J.3)
  actual_worker_id?: string | null;
  actual_machine_id?: string | null;
  planned_worker_id?: string | null;
  planned_machine_id?: string | null;
  planned_worker_name?: string | null;
  planned_machine_name?: string | null;

  // Resource validation & eligibility flags (Phase J.3)
  worker_skill?: string | null;
  machine_type?: string | null;
  worker_eligible?: boolean | null;
  machine_compatible?: boolean | null;

  // Workflow indicators (Phase J.2)
  is_terminal?: boolean;
  can_start?: boolean;
  has_uncompleted_predecessors?: boolean;

  // Phase J.5 Controlled Rework & Quality Control
  execution_type?: 'normal' | 'rework';
  rework_of_execution_id?: string | null;
  attempt_number?: number;
  latest_qc_result?: QualityCheckResult | null;
  latest_defect_severity?: DefectSeverity | null;
  quality_gate_passed?: boolean;
}

export interface OperationExecutionTransitionRequest {
  target_status: ExecutionStatus;
  operator_notes?: string | null;
  worker_id?: string | null;
  machine_id?: string | null;
  validate_resources?: boolean | null;
}

export interface WorkerAssignmentRequest {
  worker_id: string;
}

export interface MachineAssignmentRequest {
  machine_id: string;
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

  // Workflow summary metrics (Phase J.2)
  order_status?: string | null;
  completed_count?: number;
  in_progress_count?: number;
  ready_count?: number;
  pending_count?: number;
  blocked_count?: number;
  current_step_number?: number | null;
  overall_progress_percent?: number;
}

/**
 * Phase J.4: Material Consumption & Wastage Tracking Types
 */

export type MaterialCategory = 'METAL' | 'GEMSTONE';

export interface MaterialConsumption {
  id: string;
  user_id: string;
  production_order_id: string;
  operation_execution_id: string;
  specification_material_id: string | null;
  specification_gemstone_id: string | null;
  material_type: string;
  material_name: string;
  unit: string;
  planned_quantity: number;
  actual_quantity: number;
  wastage_quantity: number;
  wastage_reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface MaterialConsumptionCreate {
  material_type?: string;
  material_name?: string;
  unit?: string;
  planned_quantity?: number;
  actual_quantity: number;
  wastage_quantity?: number;
  wastage_reason?: string | null;
  notes?: string | null;
  specification_material_id?: string | null;
  specification_gemstone_id?: string | null;
}

export interface MaterialSummaryItem {
  material_type: string;
  material_name: string;
  unit: string;
  planned_quantity: number;
  actual_quantity: number;
  wastage_quantity: number;
  net_consumed_quantity: number;
}

export interface OrderMaterialSummaryResponse {
  order_id: string;
  total_planned_quantity: number;
  total_actual_quantity: number;
  total_wastage_quantity: number;
  total_net_quantity: number;
  items: MaterialSummaryItem[];
}

/**
 * Phase J.5: Quality Control & Controlled Rework Types
 */

export type QualityCheckResult = 'PASS' | 'FAIL' | 'REWORK';
export type DefectSeverity = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface QualityCheck {
  id: string;
  user_id: string;
  production_order_id: string;
  operation_execution_id: string;
  production_step_id: string;
  result: QualityCheckResult;
  defect_severity: DefectSeverity;
  defect_type: string | null;
  notes: string | null;
  checked_by: string | null;
  checked_at: string;
  created_at: string;
  updated_at: string;
  step_number?: number | null;
  stage_name?: string | null;
  quality_checkpoint?: string | null;
}

export interface QualityCheckCreate {
  result: QualityCheckResult;
  defect_severity?: DefectSeverity;
  defect_type?: string | null;
  notes?: string | null;
  checked_by?: string | null;
}

export interface ExecutionQualitySummaryItem {
  execution_id: string;
  step_id: string;
  step_number?: number | null;
  stage_name?: string | null;
  execution_type: string;
  attempt_number: number;
  execution_status: string;
  latest_qc_result: string | null;
  latest_defect_severity: string | null;
  total_checks: number;
  has_passed: boolean;
}

export interface OrderQualitySummaryResponse {
  order_id: string;
  total_operations: number;
  completed_operations: number;
  passed: number;
  failed: number;
  rework: number;
  pending_quality_checks: number;
  quality_gate_passed: boolean;
  items: ExecutionQualitySummaryItem[];
}

export interface ReworkExecutionCreate {
  operator_notes?: string | null;
}
