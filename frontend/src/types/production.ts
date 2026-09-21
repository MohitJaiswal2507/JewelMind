/**
 * Production Management TypeScript Types & Constants
 */

export type OrderPriority = 'low' | 'medium' | 'high' | 'urgent';

export const ORDER_PRIORITIES: { label: string; value: OrderPriority; color: string }[] = [
  { label: 'Low', value: 'low', color: 'bg-slate-500/20 text-slate-300 border-slate-700' },
  { label: 'Medium', value: 'medium', color: 'bg-blue-500/20 text-blue-300 border-blue-700/50' },
  { label: 'High', value: 'high', color: 'bg-amber-500/20 text-amber-300 border-amber-700/50' },
  { label: 'Urgent', value: 'urgent', color: 'bg-rose-500/20 text-rose-300 border-rose-700/50' },
];

export type OrderStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export const ORDER_STATUSES: { label: string; value: OrderStatus; color: string }[] = [
  { label: 'Pending', value: 'pending', color: 'bg-amber-500/20 text-amber-300 border-amber-700/50' },
  { label: 'In Progress', value: 'in_progress', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-700/50' },
  { label: 'Completed', value: 'completed', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-700/50' },
  { label: 'Cancelled', value: 'cancelled', color: 'bg-slate-500/20 text-slate-400 border-slate-700' },
];

export const WORKER_SKILLS: { label: string; value: string }[] = [
  { label: 'CAD Design & Modeling', value: 'cad_design' },
  { label: 'Metal Casting', value: 'casting' },
  { label: 'Stone Setting (Pavé / Prong)', value: 'stone_setting' },
  { label: 'Fine Polishing & Finishing', value: 'polishing' },
  { label: 'Laser & Hand Engraving', value: 'engraving' },
  { label: 'General Goldsmithing', value: 'general' },
];

export const MACHINE_TYPES: { label: string; value: string }[] = [
  { label: 'Fiber Laser Engraver', value: 'laser_engraver' },
  { label: '3D Wax Castable Printer', value: '3d_wax_printer' },
  { label: 'Vacuum Induction Casting Furnace', value: 'casting_furnace' },
  { label: '5-Axis CNC Milling Center', value: 'cnc_milling' },
  { label: 'Digital Ultrasonic Cleaner', value: 'ultrasonic_cleaner' },
  { label: 'High-Speed Polishing Lathe', value: 'polishing_lathe' },
  { label: 'General Equipment', value: 'general' },
];

export interface ProductionOrder {
  id: string;
  user_id: string;
  design_id: string;
  render_id?: string | null;
  approved_render_url?: string | null;
  quantity: number;
  priority: OrderPriority;
  status: OrderStatus;
  deadline: string;
  notes: string | null;
  is_overdue: boolean;
  design_name?: string | null;
  design_category?: string | null;
  design_thumbnail_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductionOrderCreateInput {
  design_id: string;
  render_id?: string | null;
  approved_render_url?: string | null;
  quantity: number;
  priority?: OrderPriority;
  status?: OrderStatus;
  deadline: string;
  notes?: string | null;
}

export interface ProductionOrderUpdateInput {
  render_id?: string | null;
  approved_render_url?: string | null;
  quantity?: number;
  priority?: OrderPriority;
  status?: OrderStatus;
  deadline?: string;
  notes?: string | null;
}

export interface ProductionOrderFilters {
  status?: OrderStatus | '';
  priority?: OrderPriority | '';
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ProductionOrderListResponse {
  items: ProductionOrder[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Worker {
  id: string;
  user_id: string;
  name: string;
  skill: string;
  capacity_hours_per_day: number;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkerCreateInput {
  name: string;
  skill: string;
  capacity_hours_per_day: number;
  is_available?: boolean;
}

export interface WorkerUpdateInput {
  name?: string;
  skill?: string;
  capacity_hours_per_day?: number;
  is_available?: boolean;
}

export interface WorkerListResponse {
  items: Worker[];
  total: number;
}

export interface Machine {
  id: string;
  user_id: string;
  name: string;
  machine_type: string;
  capacity_hours_per_day: number;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface MachineCreateInput {
  name: string;
  machine_type: string;
  capacity_hours_per_day: number;
  is_available?: boolean;
}

export interface MachineUpdateInput {
  name?: string;
  machine_type?: string;
  capacity_hours_per_day?: number;
  is_available?: boolean;
}

export interface MachineListResponse {
  items: Machine[];
  total: number;
}

export interface ProductionSummary {
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  overdue_orders: number;
  total_workers: number;
  available_workers: number;
  total_worker_capacity_hours: number;
  total_machines: number;
  available_machines: number;
  total_machine_capacity_hours: number;
}

export type SolverStatus = 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' | 'MODEL_INVALID' | 'UNKNOWN';

export interface ScheduledTask {
  id?: string;
  order_id: string;
  design_id?: string | null;
  design_name?: string | null;
  design_image_url?: string | null;
  quantity: number;
  priority: OrderPriority;
  worker_id?: string | null;
  worker_name?: string | null;
  worker_skill?: string | null;
  machine_id?: string | null;
  machine_name?: string | null;
  machine_type?: string | null;
  operation_name: string;
  start_time: string;
  end_time: string;
  start_hour?: number;
  end_hour?: number;
  duration_hours: number;
  sequence_order: number;
  is_overdue: boolean;
}

export interface OptimizationMetrics {
  makespan_hours: number;
  total_orders_scheduled: number;
  total_orders_unscheduled: number;
  worker_utilization_pct: number;
  machine_utilization_pct: number;
  orders_on_time: number;
  orders_overdue: number;
  solver_runtime_ms: number;
}

export interface OptimizationRequest {
  order_ids?: string[];
  start_date?: string;
  horizon_days?: number;
  time_limit_seconds?: number;
  persist_schedule?: boolean;
  schedule_name?: string;
}

export interface OptimizationResponse {
  status: 'success' | 'feasible' | 'infeasible' | 'error';
  solver_status: SolverStatus;
  message: string;
  schedule: ScheduledTask[];
  unscheduled_order_ids: string[];
  metrics: OptimizationMetrics;
  infeasibility_reasons: string[];
  schedule_id?: string | null;
}

export interface ProductionSchedule {
  id: string;
  user_id: string;
  name: string;
  start_date: string;
  horizon_days: number;
  solver_status: SolverStatus;
  makespan_hours: number;
  total_orders_scheduled: number;
  total_orders_unscheduled: number;
  worker_utilization_pct: number;
  machine_utilization_pct: number;
  runtime_seconds: number;
  tasks: ScheduledTask[];
  created_at: string;
  updated_at: string;
}

export interface ProductionScheduleListResponse {
  items: ProductionSchedule[];
  total: number;
}
