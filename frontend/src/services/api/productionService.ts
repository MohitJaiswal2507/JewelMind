/**
 * Production Management API Client Service
 */

import apiClient from './client';
import {
  Machine,
  MachineCreateInput,
  MachineListResponse,
  MachineUpdateInput,
  ProductionOrder,
  ProductionOrderCreateInput,
  ProductionOrderCreateFromSpecificationInput,
  ProductionOrderFilters,
  ProductionOrderListResponse,
  ProductionOrderUpdateInput,
  ProductionSummary,
  Worker,
  WorkerCreateInput,
  WorkerListResponse,
  WorkerUpdateInput,
} from '../../types/production';

export class ProductionService {
  /**
   * Retrieves aggregated production KPI summary metrics.
   */
  public async getSummary(): Promise<ProductionSummary> {
    return apiClient.get<ProductionSummary>('/api/v1/production/summary');
  }

  // -------------------------------------------------------------------------
  // Orders
  // -------------------------------------------------------------------------

  /**
   * Retrieves paginated production orders with optional filtering.
   */
  public async getOrders(filters?: ProductionOrderFilters): Promise<ProductionOrderListResponse> {
    const params: Record<string, string | number | boolean | undefined> = {};

    if (filters?.status) {
      params.status = filters.status;
    }
    if (filters?.priority) {
      params.priority = filters.priority;
    }
    if (filters?.search && filters.search.trim()) {
      params.search = filters.search.trim();
    }
    if (filters?.page) {
      params.page = filters.page;
    }
    if (filters?.page_size) {
      params.page_size = filters.page_size;
    }

    return apiClient.get<ProductionOrderListResponse>('/api/v1/production/orders', { params });
  }

  /**
   * Retrieves a single production order by ID.
   */
  public async getOrder(id: string): Promise<ProductionOrder> {
    return apiClient.get<ProductionOrder>(`/api/v1/production/orders/${id}`);
  }

  /**
   * Creates a new production order linked to an existing design.
   */
  public async createOrder(data: ProductionOrderCreateInput): Promise<ProductionOrder> {
    return apiClient.post<ProductionOrder>('/api/v1/production/orders', data);
  }

  /**
   * Creates an authoritative production order derived strictly from an approved specification.
   */
  public async createOrderFromSpecification(
    data: ProductionOrderCreateFromSpecificationInput
  ): Promise<ProductionOrder> {
    return apiClient.post<ProductionOrder>('/api/v1/production/orders/from-specification', data);
  }

  /**
   * Updates an existing production order.
   */
  public async updateOrder(id: string, data: ProductionOrderUpdateInput): Promise<ProductionOrder> {
    return apiClient.patch<ProductionOrder>(`/api/v1/production/orders/${id}`, data);
  }

  /**
   * Deletes a production order.
   */
  public async deleteOrder(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/production/orders/${id}`);
  }

  // -------------------------------------------------------------------------
  // Workers
  // -------------------------------------------------------------------------

  /**
   * Retrieves all workshop workers.
   */
  public async getWorkers(): Promise<WorkerListResponse> {
    return apiClient.get<WorkerListResponse>('/api/v1/production/workers');
  }

  /**
   * Retrieves a worker by ID.
   */
  public async getWorker(id: string): Promise<Worker> {
    return apiClient.get<Worker>(`/api/v1/production/workers/${id}`);
  }

  /**
   * Registers a new workshop worker.
   */
  public async createWorker(data: WorkerCreateInput): Promise<Worker> {
    return apiClient.post<Worker>('/api/v1/production/workers', data);
  }

  /**
   * Updates a worker's skill, availability, or capacity.
   */
  public async updateWorker(id: string, data: WorkerUpdateInput): Promise<Worker> {
    return apiClient.patch<Worker>(`/api/v1/production/workers/${id}`, data);
  }

  /**
   * Deletes a worker record.
   */
  public async deleteWorker(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/production/workers/${id}`);
  }

  // -------------------------------------------------------------------------
  // Machines
  // -------------------------------------------------------------------------

  /**
   * Retrieves all workshop machines.
   */
  public async getMachines(): Promise<MachineListResponse> {
    return apiClient.get<MachineListResponse>('/api/v1/production/machines');
  }

  /**
   * Retrieves a machine by ID.
   */
  public async getMachine(id: string): Promise<Machine> {
    return apiClient.get<Machine>(`/api/v1/production/machines/${id}`);
  }

  /**
   * Registers a new workshop machine.
   */
  public async createMachine(data: MachineCreateInput): Promise<Machine> {
    return apiClient.post<Machine>('/api/v1/production/machines', data);
  }

  /**
   * Updates a machine's type, availability, or capacity.
   */
  public async updateMachine(id: string, data: MachineUpdateInput): Promise<Machine> {
    return apiClient.patch<Machine>(`/api/v1/production/machines/${id}`, data);
  }

  /**
   * Deletes a machine record.
   */
  public async deleteMachine(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/production/machines/${id}`);
  }

  // -------------------------------------------------------------------------
  // Optimization & Schedules (OR-Tools CP-SAT)
  // -------------------------------------------------------------------------

  /**
   * Generates an optimized production schedule using OR-Tools CP-SAT.
   */
  public async optimizeProduction(data: import('../../types/production').OptimizationRequest): Promise<import('../../types/production').OptimizationResponse> {
    return apiClient.post<import('../../types/production').OptimizationResponse>('/api/v1/production/optimize', data);
  }

  /**
   * Retrieves paginated saved production schedules.
   */
  public async getSchedules(limit: number = 20, offset: number = 0): Promise<import('../../types/production').ProductionScheduleListResponse> {
    return apiClient.get<import('../../types/production').ProductionScheduleListResponse>('/api/v1/production/schedules', {
      params: { limit, offset },
    });
  }

  /**
   * Retrieves a specific saved production schedule with all task allocations.
   */
  public async getSchedule(id: string): Promise<import('../../types/production').ProductionSchedule> {
    return apiClient.get<import('../../types/production').ProductionSchedule>(`/api/v1/production/schedules/${id}`);
  }

  /**
   * Deletes a saved production schedule.
   */
  public async deleteSchedule(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/production/schedules/${id}`);
  }
}

export const productionService = new ProductionService();
export default productionService;
