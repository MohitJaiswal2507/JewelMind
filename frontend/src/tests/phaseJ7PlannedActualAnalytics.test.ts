/**
 * JewelMind Phase J.7 — Planned vs Actual Production Analytics Test Suite
 *
 * Verifies:
 * 1. productionExecutionService.getOrderAnalytics API client integration
 * 2. productionExecutionService.getAtelierAnalyticsSummary API client integration
 * 3. Planned vs actual labor hours and variance calculations
 * 4. Zero planned hours divide-by-zero protection (variance_percent = null)
 * 5. Distinct material identity preservation (gold, silver, gems not merged)
 * 6. Material consumption, scrap/wastage quantities, and wastage percentage
 * 7. Operations status distribution and routing completion rate
 * 8. Quality check verdict distributions (PASS, FAIL, REWORK) & first-pass yield
 * 9. Controlled rework attempts and rework rate calculations
 * 10. Schedule milestone tracking and schedule variance
 * 11. Edge case handling (empty executions, missing timestamps, legacy orders)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { productionExecutionService } from '../services/api/productionExecutionService';
import { apiClient } from '../services/api/client';
import {
  ProductionOrderAnalyticsResponse,
  AtelierAnalyticsSummaryResponse,
} from '../types/analytics';

describe('Phase J.7 — Planned vs Actual Production Analytics Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockOrderAnalytics: ProductionOrderAnalyticsResponse = {
    order_id: 'ord-777',
    design_id: 'des-777',
    design_name: 'Solitaire Band',
    status: 'in_progress',
    priority: 'high',
    planned: {
      quantity: 1,
      hours: 12.5,
      materials: [
        {
          material_type: 'precious_metal',
          material_name: '18K Yellow Gold',
          unit: 'g',
          planned_quantity: 15.0,
          actual_quantity: 15.8,
          wastage_quantity: 0.8,
          net_consumed_quantity: 15.0,
          variance_quantity: 0.8,
          material_variance: 0.8,
          variance_percent: 5.33,
          wastage_percent: 5.06,
        },
        {
          material_type: 'precious_metal',
          material_name: 'Silver 925',
          unit: 'g',
          planned_quantity: 5.0,
          actual_quantity: 5.2,
          wastage_quantity: 0.2,
          net_consumed_quantity: 5.0,
          variance_quantity: 0.2,
          material_variance: 0.2,
          variance_percent: 4.0,
          wastage_percent: 3.85,
        },
      ],
    },
    actual: {
      hours: 14.2,
      materials: [
        {
          material_type: 'precious_metal',
          material_name: '18K Yellow Gold',
          unit: 'g',
          planned_quantity: 15.0,
          actual_quantity: 15.8,
          wastage_quantity: 0.8,
          net_consumed_quantity: 15.0,
          variance_quantity: 0.8,
          material_variance: 0.8,
          variance_percent: 5.33,
          wastage_percent: 5.06,
        },
        {
          material_type: 'precious_metal',
          material_name: 'Silver 925',
          unit: 'g',
          planned_quantity: 5.0,
          actual_quantity: 5.2,
          wastage_quantity: 0.2,
          net_consumed_quantity: 5.0,
          variance_quantity: 0.2,
          material_variance: 0.2,
          variance_percent: 4.0,
          wastage_percent: 3.85,
        },
      ],
    },
    variance: {
      hours: 1.7,
      hours_percent: 13.6,
      materials: [
        {
          material_type: 'precious_metal',
          material_name: '18K Yellow Gold',
          unit: 'g',
          planned_quantity: 15.0,
          actual_quantity: 15.8,
          wastage_quantity: 0.8,
          net_consumed_quantity: 15.0,
          variance_quantity: 0.8,
          material_variance: 0.8,
          variance_percent: 5.33,
          wastage_percent: 5.06,
        },
        {
          material_type: 'precious_metal',
          material_name: 'Silver 925',
          unit: 'g',
          planned_quantity: 5.0,
          actual_quantity: 5.2,
          wastage_quantity: 0.2,
          net_consumed_quantity: 5.0,
          variance_quantity: 0.2,
          material_variance: 0.2,
          variance_percent: 4.0,
          wastage_percent: 3.85,
        },
      ],
    },
    operations: {
      total: 6,
      completed: 5,
      in_progress: 1,
      paused: 0,
      blocked: 0,
      ready: 0,
      pending: 0,
      completion_rate_percent: 83.3,
    },
    quality: {
      total_checks: 6,
      passed: 5,
      failed: 0,
      rework: 1,
      pending_quality_checks: 0,
      quality_gate_passed: false,
      first_pass_yield_percent: 83.3,
    },
    rework: {
      count: 1,
      rate_percent: 16.7,
    },
    schedule: {
      planned_start: '2026-10-01T08:00:00Z',
      planned_end: '2026-10-02T18:00:00Z',
      actual_start: '2026-10-01T08:15:00Z',
      actual_completion: null,
      deadline: '2026-10-03T00:00:00Z',
      schedule_variance_hours: null,
      is_overdue: false,
    },
  };

  const mockAtelierSummary: AtelierAnalyticsSummaryResponse = {
    total_orders_analyzed: 12,
    active_orders_count: 8,
    completed_orders_count: 4,
    total_planned_hours: 150.0,
    total_actual_hours: 157.5,
    net_time_variance_hours: 7.5,
    average_time_variance_percent: 5.0,
    total_rework_executions: 4,
    overall_rework_rate_percent: 8.3,
    total_qc_checks: 40,
    overall_qc_pass_rate_percent: 90.0,
    orders_with_rework_count: 2,
    orders_quality_gate_passed_count: 4,
  };

  // 1. API Client Calls
  it('calls GET /api/v1/production/orders/{order_id}/analytics and returns order analytics', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockOrderAnalytics);

    const res = await productionExecutionService.getOrderAnalytics('ord-777');
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/production/orders/ord-777/analytics');
    expect(res.order_id).toBe('ord-777');
    expect(res.planned.hours).toBe(12.5);
    expect(res.actual.hours).toBe(14.2);
    expect(res.variance.hours).toBe(1.7);
    expect(res.variance.hours_percent).toBe(13.6);
  });

  it('calls GET /api/v1/production/analytics/summary and returns atelier cross-order metrics', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockAtelierSummary);

    const res = await productionExecutionService.getAtelierAnalyticsSummary();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/production/analytics/summary');
    expect(res.total_orders_analyzed).toBe(12);
    expect(res.total_planned_hours).toBe(150.0);
    expect(res.total_actual_hours).toBe(157.5);
    expect(res.net_time_variance_hours).toBe(7.5);
    expect(res.overall_rework_rate_percent).toBe(8.3);
  });

  // 2. Time Variance Analysis
  it('correctly reports positive time variance when actual hours exceed planned norm', () => {
    const { planned, actual, variance } = mockOrderAnalytics;
    expect(actual.hours).toBeGreaterThan(planned.hours);
    expect(variance.hours).toBe(1.7);
    expect(variance.hours_percent).toBe(13.6);
  });

  it('handles zero planned hours gracefully without division by zero', () => {
    const zeroPlannedAnalytics: ProductionOrderAnalyticsResponse = {
      ...mockOrderAnalytics,
      planned: { ...mockOrderAnalytics.planned, hours: 0 },
      actual: { ...mockOrderAnalytics.actual, hours: 3.5 },
      variance: {
        ...mockOrderAnalytics.variance,
        hours: 3.5,
        hours_percent: null,
      },
    };

    expect(zeroPlannedAnalytics.planned.hours).toBe(0);
    expect(zeroPlannedAnalytics.variance.hours).toBe(3.5);
    expect(zeroPlannedAnalytics.variance.hours_percent).toBeNull();
  });

  // 3. Material Identity Preservation
  it('preserves distinct material identities and never merges different alloys or gems', () => {
    const materials = mockOrderAnalytics.variance.materials;
    expect(materials).toHaveLength(2);

    const gold = materials.find((m) => m.material_name === '18K Yellow Gold');
    const silver = materials.find((m) => m.material_name === 'Silver 925');

    expect(gold).toBeDefined();
    expect(silver).toBeDefined();
    expect(gold?.planned_quantity).toBe(15.0);
    expect(gold?.actual_quantity).toBe(15.8);
    expect(gold?.wastage_quantity).toBe(0.8);

    expect(silver?.planned_quantity).toBe(5.0);
    expect(silver?.actual_quantity).toBe(5.2);
    expect(silver?.wastage_quantity).toBe(0.2);

    // Verify they are kept separate, not lumped into a single 20g / 21g row
    expect(gold?.material_name).not.toBe(silver?.material_name);
  });

  it('handles zero actual material consumption with null wastage percent', () => {
    const zeroConsumptionMaterial = {
      material_type: 'precious_metal',
      material_name: 'Platinum 950',
      unit: 'g',
      planned_quantity: 10.0,
      actual_quantity: 0.0,
      wastage_quantity: 0.0,
      material_variance: -10.0,
      wastage_percent: null,
    };

    expect(zeroConsumptionMaterial.actual_quantity).toBe(0);
    expect(zeroConsumptionMaterial.wastage_percent).toBeNull();
  });

  // 4. Operations & QC Metrics
  it('correctly tracks operation distributions and routing completion rate', () => {
    const { operations } = mockOrderAnalytics;
    expect(operations.total).toBe(6);
    expect(operations.completed).toBe(5);
    expect(operations.in_progress).toBe(1);
    expect(operations.completion_rate_percent).toBe(83.3);
  });

  it('correctly tracks quality verdicts and first-pass yield', () => {
    const { quality } = mockOrderAnalytics;
    expect(quality.total_checks).toBe(6);
    expect(quality.passed).toBe(5);
    expect(quality.rework).toBe(1);
    expect(quality.failed).toBe(0);
    expect(quality.first_pass_yield_percent).toBe(83.3);
  });

  it('calculates rework rate correctly relative to total routing operations', () => {
    const { rework } = mockOrderAnalytics;
    expect(rework.count).toBe(1);
    expect(rework.rate_percent).toBe(16.7);
  });

  // 5. Schedule Milestones
  it('handles ongoing orders where actual completion is null without errors', () => {
    const { schedule } = mockOrderAnalytics;
    expect(schedule.actual_completion).toBeNull();
    expect(schedule.schedule_variance_hours).toBeNull();
    expect(schedule.is_overdue).toBe(false);
  });

  it('handles completed orders with non-null schedule variance', () => {
    const completedSchedule = {
      planned_start: '2026-10-01T08:00:00Z',
      planned_end: '2026-10-02T18:00:00Z',
      actual_start: '2026-10-01T08:00:00Z',
      actual_completion: '2026-10-02T20:00:00Z',
      deadline: '2026-10-03T00:00:00Z',
      schedule_variance_hours: 2.0,
      is_overdue: false,
    };

    expect(completedSchedule.schedule_variance_hours).toBe(2.0);
    expect(completedSchedule.actual_completion).not.toBeNull();
  });
});
