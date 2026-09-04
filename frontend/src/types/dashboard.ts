/**
 * Dashboard Types for JewelMind Phase 13.
 */

export interface DashboardUserSummary {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface DashboardKpis {
  total_designs: number;
  active_designs: number;
  draft_designs: number;
  rendered_designs: number;
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  overdue_orders: number;
  total_workers: number;
  available_workers: number;
  total_worker_capacity_hours: number;
  total_machines: number;
  available_machines: number;
  total_machine_capacity_hours: number;
  workshop_utilization_pct: number;
  on_time_delivery_rate: number;
}

export interface DistributionItem {
  name: string;
  count: number;
  percentage: number;
}

export interface DashboardRecentAsset {
  id: string;
  name: string;
  category: string;
  status: string;
  sketch_image_url: string | null;
  rendered_image_url: string | null;
  ai_prompt: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardDeadlineOrder {
  id: string;
  design_id: string;
  design_name?: string | null;
  design_category?: string | null;
  design_thumbnail_url?: string | null;
  quantity: number;
  priority: string;
  status: string;
  deadline: string;
  is_overdue: boolean;
}

export interface DashboardLatestSchedule {
  id: string;
  name: string;
  solver_status: string;
  makespan_hours: number;
  total_orders_scheduled: number;
  total_orders_unscheduled: number;
  worker_utilization_pct: number;
  machine_utilization_pct: number;
  horizon_days: number;
  runtime_seconds: number;
  created_at: string;
}

export interface SystemHealthStatus {
  backend: string;
  database: string;
  ai_services: string;
  active_gpu: string;
}

export interface DashboardOverviewResponse {
  user: DashboardUserSummary;
  kpis: DashboardKpis;
  categories: DistributionItem[];
  statuses: DistributionItem[];
  priorities: DistributionItem[];
  recent_designs: DashboardRecentAsset[];
  recent_renders: DashboardRecentAsset[];
  upcoming_deadlines: DashboardDeadlineOrder[];
  latest_schedule: DashboardLatestSchedule | null;
  system_status: SystemHealthStatus;
}
