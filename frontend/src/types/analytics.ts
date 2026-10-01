/**
 * Production Analytics TypeScript Definitions (Phase J.7)
 * Defines planned vs actual variance, materials, operations, quality, and schedule types.
 */

export interface MaterialVarianceItem {
  material_type: string;
  material_name: string;
  unit: string;
  planned_quantity: number;
  actual_quantity: number;
  wastage_quantity: number;
  net_consumed_quantity: number;
  variance_quantity: number;
  material_variance: number;
  variance_percent: number | null;
  wastage_percent: number | null;
}

export interface PlannedOrderAnalytics {
  quantity: number;
  hours: number;
  materials: MaterialVarianceItem[];
}

export interface ActualOrderAnalytics {
  hours: number;
  materials: MaterialVarianceItem[];
}

export interface VarianceOrderAnalytics {
  hours: number;
  hours_percent: number | null;
  materials: MaterialVarianceItem[];
}

export interface OperationsOrderAnalytics {
  total: number;
  completed: number;
  in_progress: number;
  paused: number;
  blocked: number;
  ready: number;
  pending: number;
  completion_rate_percent: number;
}

export interface QualityOrderAnalytics {
  total_checks: number;
  passed: number;
  failed: number;
  rework: number;
  pending_quality_checks: number;
  quality_gate_passed: boolean;
  first_pass_yield_percent: number | null;
}

export interface ReworkOrderAnalytics {
  count: number;
  rate_percent: number;
}

export interface ScheduleOrderAnalytics {
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_completion: string | null;
  deadline: string | null;
  schedule_variance_hours: number | null;
  is_overdue: boolean;
}

export interface ProductionOrderAnalyticsResponse {
  order_id: string;
  design_id: string;
  design_name: string | null;
  status: string;
  priority: string;
  planned: PlannedOrderAnalytics;
  actual: ActualOrderAnalytics;
  variance: VarianceOrderAnalytics;
  operations: OperationsOrderAnalytics;
  quality: QualityOrderAnalytics;
  rework: ReworkOrderAnalytics;
  schedule: ScheduleOrderAnalytics;
}

export interface AtelierAnalyticsSummaryResponse {
  total_orders_analyzed: number;
  active_orders_count: number;
  completed_orders_count: number;
  total_planned_hours: number;
  total_actual_hours: number;
  net_time_variance_hours: number;
  average_time_variance_percent: number | null;
  total_rework_executions: number;
  overall_rework_rate_percent: number;
  total_qc_checks: number;
  overall_qc_pass_rate_percent: number | null;
  orders_with_rework_count: number;
  orders_quality_gate_passed_count: number;
}
