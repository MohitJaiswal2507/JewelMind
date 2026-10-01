/**
 * Production Execution API Service (Phase J.1 Foundation)
 * Client service for initializing, listing, inspecting, and transitioning
 * shop-floor manufacturing operations (OperationExecution).
 */

import { apiClient } from './client';
import {
  MaterialConsumption,
  MaterialConsumptionCreate,
  OperationExecution,
  OperationExecutionListResponse,
  OperationExecutionTransitionRequest,
  OrderMaterialSummaryResponse,
  OrderQualitySummaryResponse,
  QualityCheck,
  QualityCheckCreate,
  ReworkExecutionCreate,
} from '../../types/execution';

class ProductionExecutionService {
  /**
   * Initializes shop-floor execution records for a spec-backed production order.
   * Sets Step 1 to READY and subsequent steps to PENDING.
   */
  async initializeOrderExecutions(orderId: string): Promise<OperationExecution[]> {
    return apiClient.post<OperationExecution[]>(
      `/api/v1/production/orders/${orderId}/executions/initialize`,
      {}
    );
  }

  /**
   * Retrieves all operation execution records for a production order,
   * sorted by routing step number.
   */
  async getOrderExecutions(orderId: string): Promise<OperationExecutionListResponse> {
    return apiClient.get<OperationExecutionListResponse>(
      `/api/v1/production/orders/${orderId}/executions`
    );
  }

  /**
   * Retrieves full details for a single operation execution record.
   */
  async getExecution(executionId: string): Promise<OperationExecution> {
    return apiClient.get<OperationExecution>(
      `/api/v1/production/executions/${executionId}`
    );
  }

  /**
   * Transitions an operation execution state (e.g. READY -> IN_PROGRESS,
   * IN_PROGRESS -> PAUSED, IN_PROGRESS -> COMPLETED).
   */
  async transitionExecution(
    executionId: string,
    req: OperationExecutionTransitionRequest
  ): Promise<OperationExecution> {
    return apiClient.post<OperationExecution>(
      `/api/v1/production/executions/${executionId}/transition`,
      req
    );
  }

  /**
   * Assigns an eligible workshop artisan to an operation execution.
   */
  async assignWorker(
    executionId: string,
    workerId: string
  ): Promise<OperationExecution> {
    return apiClient.post<OperationExecution>(
      `/api/v1/production/executions/${executionId}/assign-worker`,
      { worker_id: workerId }
    );
  }

  /**
   * Assigns compatible equipment to an operation execution.
   */
  async assignMachine(
    executionId: string,
    machineId: string
  ): Promise<OperationExecution> {
    return apiClient.post<OperationExecution>(
      `/api/v1/production/executions/${executionId}/assign-machine`,
      { machine_id: machineId }
    );
  }

  /**
   * Records actual material consumption against an operation execution (Phase J.4).
   */
  async recordMaterialConsumption(
    executionId: string,
    payload: MaterialConsumptionCreate
  ): Promise<MaterialConsumption> {
    return apiClient.post<MaterialConsumption>(
      `/api/v1/production/executions/${executionId}/material-consumption`,
      payload
    );
  }

  /**
   * Lists all material consumption records for an operation execution (Phase J.4).
   */
  async getExecutionMaterialConsumptions(
    executionId: string
  ): Promise<MaterialConsumption[]> {
    return apiClient.get<MaterialConsumption[]>(
      `/api/v1/production/executions/${executionId}/material-consumption`
    );
  }

  /**
   * Lists all material consumption records for a production order (Phase J.4).
   */
  async getOrderMaterialConsumptions(
    orderId: string
  ): Promise<MaterialConsumption[]> {
    return apiClient.get<MaterialConsumption[]>(
      `/api/v1/production/orders/${orderId}/material-consumption`
    );
  }

  /**
   * Retrieves planned vs actual material consumption summary for an order (Phase J.4).
   */
  async getOrderMaterialSummary(
    orderId: string
  ): Promise<OrderMaterialSummaryResponse> {
    return apiClient.get<OrderMaterialSummaryResponse>(
      `/api/v1/production/orders/${orderId}/material-summary`
    );
  }

  // =========================================================================
  // Phase J.5: Quality Control & Controlled Rework Methods
  // =========================================================================

  /**
   * Records a quality inspection outcome (PASS, FAIL, REWORK) for a completed operation execution.
   */
  async recordQualityCheck(
    executionId: string,
    payload: QualityCheckCreate
  ): Promise<QualityCheck> {
    return apiClient.post<QualityCheck>(
      `/api/v1/production/executions/${executionId}/quality-check`,
      payload
    );
  }

  /**
   * Retrieves complete chronological quality inspection records for an execution step.
   */
  async getExecutionQualityChecks(
    executionId: string
  ): Promise<QualityCheck[]> {
    return apiClient.get<QualityCheck[]>(
      `/api/v1/production/executions/${executionId}/quality-check`
    );
  }

  /**
   * Authorizes and initializes a controlled rework OperationExecution following a REWORK QC outcome.
   */
  async createReworkExecution(
    executionId: string,
    payload?: ReworkExecutionCreate
  ): Promise<OperationExecution> {
    return apiClient.post<OperationExecution>(
      `/api/v1/production/executions/${executionId}/rework`,
      payload || {}
    );
  }

  /**
   * Retrieves concise quality gate summary and completion status for a production order.
   */
  async getOrderQualitySummary(
    orderId: string
  ): Promise<OrderQualitySummaryResponse> {
    return apiClient.get<OrderQualitySummaryResponse>(
      `/api/v1/production/orders/${orderId}/quality-checks`
    );
  }

  /**
   * Explicitly completes a production order upon verifying 100% passing quality checks.
   */
  async completeOrder(
    orderId: string
  ): Promise<{ order_id: string; status: string; message: string }> {
    return apiClient.post<{ order_id: string; status: string; message: string }>(
      `/api/v1/production/orders/${orderId}/complete`,
      {}
    );
  }
}

export const productionExecutionService = new ProductionExecutionService();
