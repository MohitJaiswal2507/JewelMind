/**
 * Health & Diagnostics Service
 */

import { apiClient } from './client';
import { HealthResponse, DatabaseHealthResponse } from '../../types/api';

export const healthService = {
  /**
   * Fetch API V1 health status
   */
  getHealth(): Promise<HealthResponse> {
    return apiClient.get<HealthResponse>('/api/v1/health', { timeoutMs: 3000 });
  },

  /**
   * Fetch database connectivity status
   */
  getDbHealth(): Promise<DatabaseHealthResponse> {
    return apiClient.get<DatabaseHealthResponse>('/api/v1/health/db', { timeoutMs: 3000 });
  },
};

export default healthService;
