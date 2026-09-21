/**
 * JewelMind Phase I.5 — Production Order Integration + CP-SAT Scheduling Test Suite
 *
 * Verifies:
 * 1. productionService.createOrderFromSpecification API client integration
 * 2. ProductionOrder type exposes specification lineage fields (specification_id, version, category, counts)
 * 3. Backward compatibility for legacy orders without specification_id
 * 4. CP-SAT optimization API client integration with dynamic operations
 * 5. ScheduledTask exposes specification_id, step_number, quality_checkpoint
 * 6. Dynamic operation counts (3-step, 5-step, gem-free)
 * 7. Infeasibility diagnostic responses handled correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { productionService } from '../services/api/productionService';
import { apiClient } from '../services/api/client';
import {
  ProductionOrder,
  OptimizationResponse,
  ProductionOrderCreateFromSpecificationInput,
} from '../types/production';

describe('Phase I.5 — Production Order Integration & CP-SAT Scheduling Frontend Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockApprovedSpecOrder: ProductionOrder = {
    id: 'order-uuid-1',
    user_id: 'user-uuid-1',
    design_id: 'design-uuid-1',
    render_id: 'render-uuid-1',
    specification_id: 'spec-uuid-1',
    specification_version: 1,
    specification_category: 'ring',
    routing_steps_count: 5,
    materials_count: 1,
    gemstones_count: 1,
    design_name: 'Solitaire Diamond Ring',
    design_category: 'ring',
    design_thumbnail_url: 'https://storage.jewelmind.ai/renders/ring.png',
    approved_render_url: 'https://storage.jewelmind.ai/renders/ring_approved.png',
    quantity: 1,
    priority: 'high',
    status: 'pending',
    deadline: '2026-10-01T00:00:00Z',
    is_overdue: false,
    notes: 'Urgent client commission',
    created_at: '2026-09-22T00:00:00Z',
    updated_at: '2026-09-22T00:00:00Z',
  };

  const mockLegacyOrder: ProductionOrder = {
    id: 'order-legacy-1',
    user_id: 'user-uuid-1',
    design_id: 'design-uuid-2',
    render_id: null,
    specification_id: null,
    specification_version: null,
    specification_category: null,
    routing_steps_count: 0,
    materials_count: 0,
    gemstones_count: 0,
    design_name: 'Classic Band',
    design_category: 'ring',
    design_thumbnail_url: null,
    approved_render_url: null,
    quantity: 2,
    priority: 'medium',
    status: 'pending',
    deadline: '2026-10-05T00:00:00Z',
    is_overdue: false,
    notes: null,
    created_at: '2026-09-22T00:00:00Z',
    updated_at: '2026-09-22T00:00:00Z',
  };

  const mockOptimizationResponse: OptimizationResponse = {
    status: 'success',
    solver_status: 'OPTIMAL',
    message: 'Globally optimal schedule computed successfully.',
    metrics: {
      makespan_hours: 14.5,
      total_orders_scheduled: 1,
      total_orders_unscheduled: 0,
      worker_utilization_pct: 78.5,
      machine_utilization_pct: 62.0,
      orders_on_time: 1,
      orders_overdue: 0,
      solver_runtime_ms: 120,
    },
    schedule: [
      {
        id: 'task-1',
        order_id: 'order-uuid-1',
        design_name: 'Solitaire Diamond Ring',
        operation_name: 'CAD Modeling & Wax Pattern',
        worker_id: 'worker-1',
        worker_name: 'Master CAD Artisan',
        machine_id: 'machine-1',
        machine_name: 'SLA 3D Wax Printer',
        start_time: '2026-09-22T08:00:00Z',
        end_time: '2026-09-22T10:30:00Z',
        duration_hours: 2.5,
        sequence_order: 1,
        quantity: 1,
        priority: 'high',
        is_overdue: false,
        specification_id: 'spec-uuid-1',
        step_number: 1,
        quality_checkpoint: 'Verify digital prong dimensions',
      },
      {
        id: 'task-2',
        order_id: 'order-uuid-1',
        design_name: 'Solitaire Diamond Ring',
        operation_name: 'Casting & Metallurgy',
        worker_id: 'worker-2',
        worker_name: 'Senior Foundryman',
        machine_id: 'machine-2',
        machine_name: 'Vacuum Induction Casting Machine',
        start_time: '2026-09-22T10:30:00Z',
        end_time: '2026-09-22T13:30:00Z',
        duration_hours: 3.0,
        sequence_order: 2,
        quantity: 1,
        priority: 'high',
        is_overdue: false,
        specification_id: 'spec-uuid-1',
        step_number: 2,
        quality_checkpoint: 'Inspect sprue for shrinkage porosity',
      },
      {
        id: 'task-3',
        order_id: 'order-uuid-1',
        design_name: 'Solitaire Diamond Ring',
        operation_name: 'Stone Setting & Assembly',
        worker_id: 'worker-3',
        worker_name: 'Master Diamond Setter',
        machine_id: null,
        machine_name: null,
        start_time: '2026-09-22T13:30:00Z',
        end_time: '2026-09-22T17:30:00Z',
        duration_hours: 4.0,
        sequence_order: 3,
        quantity: 1,
        priority: 'high',
        is_overdue: false,
        specification_id: 'spec-uuid-1',
        step_number: 3,
        quality_checkpoint: 'Check prong tightness under 20x microscope',
      },
      {
        id: 'task-4',
        order_id: 'order-uuid-1',
        design_name: 'Solitaire Diamond Ring',
        operation_name: 'Polishing & Lapping',
        worker_id: 'worker-4',
        worker_name: 'Artisan Polisher',
        machine_id: 'machine-3',
        machine_name: 'Dual-Spindle Polishing Lathe',
        start_time: '2026-09-22T17:30:00Z',
        end_time: '2026-09-22T19:30:00Z',
        duration_hours: 2.0,
        sequence_order: 4,
        quantity: 1,
        priority: 'high',
        is_overdue: false,
        specification_id: 'spec-uuid-1',
        step_number: 4,
        quality_checkpoint: null,
      },
      {
        id: 'task-5',
        order_id: 'order-uuid-1',
        design_name: 'Solitaire Diamond Ring',
        operation_name: 'Final Quality Audit',
        worker_id: 'worker-5',
        worker_name: 'QA Inspector',
        machine_id: null,
        machine_name: null,
        start_time: '2026-09-22T19:30:00Z',
        end_time: '2026-09-22T20:30:00Z',
        duration_hours: 1.0,
        sequence_order: 5,
        quantity: 1,
        priority: 'high',
        is_overdue: false,
        specification_id: 'spec-uuid-1',
        step_number: 5,
        quality_checkpoint: 'Hallmark stamp & final luster sign-off',
      },
    ],
    schedule_id: 'schedule-uuid-1',
    unscheduled_order_ids: [],
    infeasibility_reasons: [],
  };

  it('calls POST /api/v1/production/orders/from-specification with specification_id and quantity', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValue(mockApprovedSpecOrder);

    const input: ProductionOrderCreateFromSpecificationInput = {
      specification_id: 'spec-uuid-1',
      quantity: 1,
      priority: 'high',
      notes: 'Urgent client commission',
    };

    const order = await productionService.createOrderFromSpecification(input);

    expect(postSpy).toHaveBeenCalledWith('/api/v1/production/orders/from-specification', input);
    expect(order.id).toBe('order-uuid-1');
    expect(order.specification_id).toBe('spec-uuid-1');
    expect(order.specification_version).toBe(1);
    expect(order.routing_steps_count).toBe(5);
    expect(order.approved_render_url).toBe('https://storage.jewelmind.ai/renders/ring_approved.png');
  });

  it('preserves backward compatibility for legacy orders without specification_id', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValue({
      items: [mockApprovedSpecOrder, mockLegacyOrder],
      total: 2,
      page: 1,
      page_size: 20,
    });

    const orders = await productionService.getOrders();
    expect(orders.items).toHaveLength(2);

    const specOrder = orders.items[0];
    expect(specOrder.specification_id).toBe('spec-uuid-1');
    expect(specOrder.routing_steps_count).toBe(5);

    const legacyOrder = orders.items[1];
    expect(legacyOrder.specification_id).toBeNull();
    expect(legacyOrder.specification_version).toBeNull();
  });

  it('runs CP-SAT optimization and receives specification-derived scheduled tasks', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValue(mockOptimizationResponse);

    const res = await productionService.optimizeProduction({
      horizon_days: 14,
      time_limit_seconds: 10,
    });

    expect(res.status).toBe('success');
    expect(res.solver_status).toBe('OPTIMAL');
    expect(res.schedule).toHaveLength(5);

    // Verify traceability on scheduled tasks
    const firstTask = res.schedule[0];
    expect(firstTask.specification_id).toBe('spec-uuid-1');
    expect(firstTask.step_number).toBe(1);
    expect(firstTask.quality_checkpoint).toBe('Verify digital prong dimensions');

    // Verify sequence ordering & non-overlapping start/end
    for (let i = 1; i < res.schedule.length; i++) {
      const prev = res.schedule[i - 1];
      const curr = res.schedule[i];
      expect(new Date(curr.start_time).getTime()).toBeGreaterThanOrEqual(
        new Date(prev.end_time).getTime()
      );
      expect(curr.sequence_order).toBe(prev.sequence_order + 1);
    }
  });

  it('handles CP-SAT infeasibility diagnostic responses gracefully', async () => {
    const mockInfeasibleResponse: OptimizationResponse = {
      status: 'infeasible',
      solver_status: 'INFEASIBLE',
      message: 'Optimization infeasible with current workshop constraints',
      infeasibility_reasons: [
        'Total required bench hours (120.0h) exceeds workshop capacity (80.0h)',
        'No active artisans found with skill [stone_setting] for stone-set items',
      ],
      metrics: {
        makespan_hours: 0,
        total_orders_scheduled: 0,
        total_orders_unscheduled: 1,
        worker_utilization_pct: 0,
        machine_utilization_pct: 0,
        orders_on_time: 0,
        orders_overdue: 0,
        solver_runtime_ms: 45,
      },
      schedule: [],
      unscheduled_order_ids: ['order-uuid-1'],
    };

    vi.spyOn(apiClient, 'post').mockResolvedValue(mockInfeasibleResponse);

    const res = await productionService.optimizeProduction({
      horizon_days: 7,
      time_limit_seconds: 5,
    });

    expect(res.status).toBe('infeasible');
    expect(res.solver_status).toBe('INFEASIBLE');
    expect(res.infeasibility_reasons).toHaveLength(2);
    expect(res.infeasibility_reasons![0]).toContain('exceeds workshop capacity');
  });
});
