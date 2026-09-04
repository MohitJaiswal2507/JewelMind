/**
 * Dashboard API Service for JewelMind Phase 13.
 */

import apiClient from './client';
import { DashboardOverviewResponse } from '../../types/dashboard';

export class DashboardService {
  /**
   * Retrieves aggregated dashboard metrics, portfolio summaries,
   * production KPIs, and latest CP-SAT schedules.
   */
  public async getOverview(): Promise<DashboardOverviewResponse> {
    return apiClient.get<DashboardOverviewResponse>('/api/v1/dashboard/overview');
  }
}

export const dashboardService = new DashboardService();
export default dashboardService;
