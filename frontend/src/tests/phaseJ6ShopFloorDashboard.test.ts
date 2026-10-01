/**
 * JewelMind Phase J.6 — Shop-Floor UI & Production Dashboard Test Suite
 *
 * Verifies:
 * 1. productionExecutionService integration with shop-floor operations
 * 2. Execution state transitions (READY -> IN_PROGRESS -> PAUSED -> COMPLETED -> BLOCKED)
 * 3. Resource assignment integration (artisan workers & equipment machinery)
 * 4. Append-only material consumption & scrap tracking integration
 * 5. Quality control inspections (PASS, FAIL, REWORK) and severity constraints
 * 6. Controlled rework execution authorization (attempt numbering & linkage)
 * 7. Order-level quality gate verification and final order completion
 * 8. Dashboard metrics aggregation and active order table routing
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { productionExecutionService } from '../services/api/productionExecutionService';
import { productionService } from '../services/api/productionService';
import { apiClient } from '../services/api/client';
import {
  OperationExecution,
  OperationExecutionListResponse,
  OrderMaterialSummaryResponse,
  OrderQualitySummaryResponse,
  QualityCheck,
  MaterialConsumption,
} from '../types/execution';
import {
  ProductionOrder,
  ProductionOrderListResponse,
  WorkerListResponse,
  MachineListResponse,
} from '../types/production';

describe('Phase J.6 — Shop-Floor UI & Production Dashboard Service Integration Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockOrder: ProductionOrder = {
    id: 'order-101',
    user_id: 'user-1',
    design_id: 'design-1',
    render_id: 'render-1',
    specification_id: 'spec-1',
    specification_version: 1,
    specification_category: 'ring',
    routing_steps_count: 3,
    materials_count: 2,
    gemstones_count: 1,
    design_name: 'Solitaire Gold Band',
    design_category: 'ring',
    design_thumbnail_url: null,
    approved_render_url: null,
    quantity: 1,
    priority: 'high',
    status: 'in_progress',
    deadline: '2026-10-15T00:00:00Z',
    is_overdue: false,
    notes: 'Urgent royal order',
    created_at: '2026-10-01T10:00:00Z',
    updated_at: '2026-10-01T10:00:00Z',
  };

  const mockExecutions: OperationExecution[] = [
    {
      id: 'exec-1',
      user_id: 'user-1',
      production_order_id: 'order-101',
      production_step_id: 'step-1',
      scheduled_task_id: null,
      worker_id: 'worker-1',
      machine_id: 'machine-1',
      status: 'completed',
      planned_start_time: '2026-10-01T10:00:00Z',
      planned_end_time: '2026-10-01T12:00:00Z',
      planned_duration_hours: 2.0,
      actual_start_time: '2026-10-01T10:05:00Z',
      actual_end_time: '2026-10-01T12:00:00Z',
      actual_duration_hours: 1.9,
      pause_duration_hours: 0,
      last_paused_at: null,
      completed_at: '2026-10-01T12:00:00Z',
      operator_notes: null,
      created_at: '2026-10-01T10:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
      step_number: 1,
      stage_name: 'Investment Casting',
      required_skill: 'Casting Specialist',
      required_machine_type: 'Vacuum Casting Machine',
      worker_name: 'Jean Goldsmith',
      machine_name: 'Indutherm VC400',
      execution_type: 'normal',
      attempt_number: 1,
      latest_qc_result: 'PASS',
      latest_defect_severity: 'NONE',
    },
    {
      id: 'exec-2',
      user_id: 'user-1',
      production_order_id: 'order-101',
      production_step_id: 'step-2',
      scheduled_task_id: null,
      worker_id: null,
      machine_id: null,
      status: 'ready',
      planned_start_time: '2026-10-01T12:30:00Z',
      planned_end_time: '2026-10-01T14:30:00Z',
      planned_duration_hours: 2.0,
      actual_start_time: null,
      actual_end_time: null,
      actual_duration_hours: null,
      pause_duration_hours: 0,
      last_paused_at: null,
      completed_at: null,
      operator_notes: null,
      created_at: '2026-10-01T10:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
      step_number: 2,
      stage_name: 'Stone Setting',
      required_skill: 'Stone Setter',
      required_machine_type: 'Microscope Setting Bench',
      worker_name: null,
      machine_name: null,
      execution_type: 'normal',
      attempt_number: 1,
      latest_qc_result: null,
      latest_defect_severity: null,
    },
    {
      id: 'exec-3',
      user_id: 'user-1',
      production_order_id: 'order-101',
      production_step_id: 'step-3',
      scheduled_task_id: null,
      worker_id: null,
      machine_id: null,
      status: 'pending',
      planned_start_time: '2026-10-01T15:00:00Z',
      planned_end_time: '2026-10-01T16:00:00Z',
      planned_duration_hours: 1.0,
      actual_start_time: null,
      actual_end_time: null,
      actual_duration_hours: null,
      pause_duration_hours: 0,
      last_paused_at: null,
      completed_at: null,
      operator_notes: null,
      created_at: '2026-10-01T10:00:00Z',
      updated_at: '2026-10-01T10:00:00Z',
      step_number: 3,
      stage_name: 'Ultrasonic Cleaning & Polish',
      required_skill: 'Polisher',
      required_machine_type: 'Polishing Lathe',
      worker_name: null,
      machine_name: null,
      execution_type: 'normal',
      attempt_number: 1,
      latest_qc_result: null,
      latest_defect_severity: null,
      is_terminal: true,
    },
  ];

  // ---------------------------------------------------------------------------
  // 1. Order Execution Loading & Initialization
  // ---------------------------------------------------------------------------
  it('loads order executions correctly via productionExecutionService', async () => {
    const mockListResponse: OperationExecutionListResponse = {
      order_id: 'order-101',
      total: 3,
      items: mockExecutions,
      completed_count: 1,
      ready_count: 1,
      pending_count: 1,
      overall_progress_percent: 33,
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockListResponse);

    const result = await productionExecutionService.getOrderExecutions('order-101');

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/orders/order-101/executions');
    expect(result.items).toHaveLength(3);
    expect(result.completed_count).toBe(1);
    expect(result.overall_progress_percent).toBe(33);
  });

  it('triggers execution initialization for spec-backed orders when empty', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockExecutions);

    const result = await productionExecutionService.initializeOrderExecutions('order-101');

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/orders/order-101/executions/initialize',
      {}
    );
    expect(result).toHaveLength(3);
  });

  // ---------------------------------------------------------------------------
  // 2. Execution State Transitions
  // ---------------------------------------------------------------------------
  it('transitions execution from READY to IN_PROGRESS', async () => {
    const updatedExec: OperationExecution = {
      ...mockExecutions[1],
      status: 'in_progress',
      actual_start_time: '2026-10-01T12:35:00Z',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(updatedExec);

    const res = await productionExecutionService.transitionExecution('exec-2', {
      target_status: 'in_progress',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-2/transition',
      { target_status: 'in_progress' }
    );
    expect(res.status).toBe('in_progress');
    expect(res.actual_start_time).toBe('2026-10-01T12:35:00Z');
  });

  it('transitions execution from IN_PROGRESS to PAUSED', async () => {
    const pausedExec: OperationExecution = {
      ...mockExecutions[1],
      status: 'paused',
      last_paused_at: '2026-10-01T13:00:00Z',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce(pausedExec);

    const res = await productionExecutionService.transitionExecution('exec-2', {
      target_status: 'paused',
    });

    expect(res.status).toBe('paused');
    expect(res.last_paused_at).toBe('2026-10-01T13:00:00Z');
  });

  it('transitions execution from IN_PROGRESS to COMPLETED', async () => {
    const completedExec: OperationExecution = {
      ...mockExecutions[1],
      status: 'completed',
      completed_at: '2026-10-01T14:30:00Z',
      actual_duration_hours: 1.9,
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce(completedExec);

    const res = await productionExecutionService.transitionExecution('exec-2', {
      target_status: 'completed',
    });

    expect(res.status).toBe('completed');
    expect(res.actual_duration_hours).toBe(1.9);
  });

  it('handles BLOCKED state transition with operator notes', async () => {
    const blockedExec: OperationExecution = {
      ...mockExecutions[1],
      status: 'blocked',
      operator_notes: 'Missing sapphire lot #4',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(blockedExec);

    const res = await productionExecutionService.transitionExecution('exec-2', {
      target_status: 'blocked',
      operator_notes: 'Missing sapphire lot #4',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-2/transition',
      { target_status: 'blocked', operator_notes: 'Missing sapphire lot #4' }
    );
    expect(res.status).toBe('blocked');
    expect(res.operator_notes).toBe('Missing sapphire lot #4');
  });

  // ---------------------------------------------------------------------------
  // 3. Worker & Machine Assignment Integration
  // ---------------------------------------------------------------------------
  it('assigns eligible artisan worker to operation', async () => {
    const assignedExec: OperationExecution = {
      ...mockExecutions[1],
      worker_id: 'worker-2',
      worker_name: 'Maya StoneSetter',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(assignedExec);

    const res = await productionExecutionService.assignWorker('exec-2', 'worker-2');

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-2/assign-worker',
      { worker_id: 'worker-2' }
    );
    expect(res.worker_id).toBe('worker-2');
    expect(res.worker_name).toBe('Maya StoneSetter');
  });

  it('assigns compatible machine equipment to operation', async () => {
    const assignedExec: OperationExecution = {
      ...mockExecutions[1],
      machine_id: 'machine-2',
      machine_name: 'Leica Setting Scope Station',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(assignedExec);

    const res = await productionExecutionService.assignMachine('exec-2', 'machine-2');

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-2/assign-machine',
      { machine_id: 'machine-2' }
    );
    expect(res.machine_id).toBe('machine-2');
    expect(res.machine_name).toBe('Leica Setting Scope Station');
  });

  // ---------------------------------------------------------------------------
  // 4. Quality Control (QC) Recording & History
  // ---------------------------------------------------------------------------
  it('records PASS quality check with NONE severity', async () => {
    const mockQc: QualityCheck = {
      id: 'qc-1',
      user_id: 'user-1',
      production_order_id: 'order-101',
      operation_execution_id: 'exec-1',
      production_step_id: 'step-1',
      result: 'PASS',
      defect_severity: 'NONE',
      defect_type: null,
      notes: 'Clean casting surface',
      checked_by: 'user-1',
      checked_at: '2026-10-01T12:05:00Z',
      created_at: '2026-10-01T12:05:00Z',
      updated_at: '2026-10-01T12:05:00Z',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockQc);

    const res = await productionExecutionService.recordQualityCheck('exec-1', {
      result: 'PASS',
      defect_severity: 'NONE',
      notes: 'Clean casting surface',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-1/quality-check',
      {
        result: 'PASS',
        defect_severity: 'NONE',
        notes: 'Clean casting surface',
      }
    );
    expect(res.result).toBe('PASS');
    expect(res.defect_severity).toBe('NONE');
  });

  it('records REWORK quality check with MEDIUM severity and defect type', async () => {
    const mockQc: QualityCheck = {
      id: 'qc-2',
      user_id: 'user-1',
      production_order_id: 'order-101',
      operation_execution_id: 'exec-2',
      production_step_id: 'step-2',
      result: 'REWORK',
      defect_severity: 'MEDIUM',
      defect_type: 'LOOSE_PRONG',
      notes: 'Re-tighten side prongs',
      checked_by: 'user-1',
      checked_at: '2026-10-01T14:40:00Z',
      created_at: '2026-10-01T14:40:00Z',
      updated_at: '2026-10-01T14:40:00Z',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockQc);

    const res = await productionExecutionService.recordQualityCheck('exec-2', {
      result: 'REWORK',
      defect_severity: 'MEDIUM',
      defect_type: 'LOOSE_PRONG',
      notes: 'Re-tighten side prongs',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-2/quality-check',
      {
        result: 'REWORK',
        defect_severity: 'MEDIUM',
        defect_type: 'LOOSE_PRONG',
        notes: 'Re-tighten side prongs',
      }
    );
    expect(res.result).toBe('REWORK');
    expect(res.defect_type).toBe('LOOSE_PRONG');
  });

  it('records FAIL quality check with CRITICAL severity', async () => {
    const mockQc: QualityCheck = {
      id: 'qc-3',
      user_id: 'user-1',
      production_order_id: 'order-101',
      operation_execution_id: 'exec-2',
      production_step_id: 'step-2',
      result: 'FAIL',
      defect_severity: 'CRITICAL',
      defect_type: 'CRACKED_STONE',
      notes: 'Irreparable gemstone fracture',
      checked_by: 'user-1',
      checked_at: '2026-10-01T14:45:00Z',
      created_at: '2026-10-01T14:45:00Z',
      updated_at: '2026-10-01T14:45:00Z',
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockQc);

    const res = await productionExecutionService.recordQualityCheck('exec-2', {
      result: 'FAIL',
      defect_severity: 'CRITICAL',
      defect_type: 'CRACKED_STONE',
      notes: 'Irreparable gemstone fracture',
    });

    expect(res.result).toBe('FAIL');
    expect(res.defect_severity).toBe('CRITICAL');
  });

  it('fetches chronological QC inspection records for an execution', async () => {
    const mockChecks: QualityCheck[] = [
      {
        id: 'qc-old',
        user_id: 'user-1',
        production_order_id: 'order-101',
        operation_execution_id: 'exec-2',
        production_step_id: 'step-2',
        result: 'REWORK',
        defect_severity: 'MEDIUM',
        defect_type: 'POROSITY',
        notes: 'Surface pitting',
        checked_by: 'user-1',
        checked_at: '2026-10-01T14:00:00Z',
        created_at: '2026-10-01T14:00:00Z',
        updated_at: '2026-10-01T14:00:00Z',
      },
      {
        id: 'qc-new',
        user_id: 'user-1',
        production_order_id: 'order-101',
        operation_execution_id: 'exec-2',
        production_step_id: 'step-2',
        result: 'PASS',
        defect_severity: 'NONE',
        defect_type: null,
        notes: 'Refinished perfectly',
        checked_by: 'user-1',
        checked_at: '2026-10-01T15:00:00Z',
        created_at: '2026-10-01T15:00:00Z',
        updated_at: '2026-10-01T15:00:00Z',
      },
    ];

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockChecks);

    const checks = await productionExecutionService.getExecutionQualityChecks('exec-2');

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/executions/exec-2/quality-check');
    expect(checks).toHaveLength(2);
    expect(checks[1].result).toBe('PASS');
  });

  // ---------------------------------------------------------------------------
  // 5. Controlled Rework Execution
  // ---------------------------------------------------------------------------
  it('creates explicit rework execution following REWORK QC outcome', async () => {
    const reworkExec: OperationExecution = {
      id: 'exec-2-rework',
      user_id: 'user-1',
      production_order_id: 'order-101',
      production_step_id: 'step-2',
      scheduled_task_id: null,
      worker_id: null,
      machine_id: null,
      status: 'ready',
      planned_start_time: '2026-10-01T14:45:00Z',
      planned_end_time: '2026-10-01T16:00:00Z',
      planned_duration_hours: 1.25,
      actual_start_time: null,
      actual_end_time: null,
      actual_duration_hours: null,
      pause_duration_hours: 0,
      last_paused_at: null,
      completed_at: null,
      operator_notes: 'Rework authorized after loose prong',
      created_at: '2026-10-01T14:45:00Z',
      updated_at: '2026-10-01T14:45:00Z',
      step_number: 2,
      stage_name: 'Stone Setting',
      required_skill: 'Stone Setter',
      required_machine_type: 'Microscope Setting Bench',
      worker_name: null,
      machine_name: null,
      execution_type: 'rework',
      rework_of_execution_id: 'exec-2',
      attempt_number: 2,
      latest_qc_result: null,
      latest_defect_severity: null,
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(reworkExec);

    const res = await productionExecutionService.createReworkExecution('exec-2', {
      operator_notes: 'Rework authorized after loose prong',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-2/rework',
      { operator_notes: 'Rework authorized after loose prong' }
    );
    expect(res.execution_type).toBe('rework');
    expect(res.attempt_number).toBe(2);
    expect(res.rework_of_execution_id).toBe('exec-2');
    expect(res.status).toBe('ready');
  });

  // ---------------------------------------------------------------------------
  // 6. Material Consumption & Wastage Tracking
  // ---------------------------------------------------------------------------
  it('records append-only material consumption against operation', async () => {
    const mockConsumption: MaterialConsumption = {
      id: 'mat-1',
      user_id: 'user-1',
      production_order_id: 'order-101',
      operation_execution_id: 'exec-1',
      specification_material_id: null,
      specification_gemstone_id: null,
      material_type: 'gold_18k',
      material_name: '18K Yellow Gold Grain',
      unit: 'g',
      planned_quantity: 8.2,
      actual_quantity: 8.35,
      wastage_quantity: 0.15,
      wastage_reason: 'Crucible residue and sprue cutoff',
      notes: 'Clean melt batch',
      created_at: '2026-10-01T11:00:00Z',
      updated_at: '2026-10-01T11:00:00Z',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockConsumption);

    const res = await productionExecutionService.recordMaterialConsumption('exec-1', {
      material_type: 'gold_18k',
      material_name: '18K Yellow Gold Grain',
      unit: 'g',
      planned_quantity: 8.2,
      actual_quantity: 8.35,
      wastage_quantity: 0.15,
      wastage_reason: 'Crucible residue and sprue cutoff',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/executions/exec-1/material-consumption',
      {
        material_type: 'gold_18k',
        material_name: '18K Yellow Gold Grain',
        unit: 'g',
        planned_quantity: 8.2,
        actual_quantity: 8.35,
        wastage_quantity: 0.15,
        wastage_reason: 'Crucible residue and sprue cutoff',
      }
    );
    expect(res.actual_quantity).toBe(8.35);
    expect(res.wastage_quantity).toBe(0.15);
  });

  it('fetches order planned vs actual material summary', async () => {
    const mockSummary: OrderMaterialSummaryResponse = {
      order_id: 'order-101',
      total_planned_quantity: 8.2,
      total_actual_quantity: 8.35,
      total_wastage_quantity: 0.15,
      total_net_quantity: 8.5,
      items: [
        {
          material_type: 'gold_18k',
          material_name: '18K Yellow Gold Grain',
          unit: 'g',
          planned_quantity: 8.2,
          actual_quantity: 8.35,
          wastage_quantity: 0.15,
          net_consumed_quantity: 8.5,
        },
      ],
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockSummary);

    const summary = await productionExecutionService.getOrderMaterialSummary('order-101');

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/orders/order-101/material-summary');
    expect(summary.total_actual_quantity).toBe(8.35);
    expect(summary.items).toHaveLength(1);
  });

  // ---------------------------------------------------------------------------
  // 7. Order Quality Summary & Quality Gate Completion
  // ---------------------------------------------------------------------------
  it('retrieves order quality gate status with passing summary', async () => {
    const mockQcSummary: OrderQualitySummaryResponse = {
      order_id: 'order-101',
      total_operations: 3,
      completed_operations: 3,
      passed: 3,
      failed: 0,
      rework: 0,
      pending_quality_checks: 0,
      quality_gate_passed: true,
      items: [
        {
          execution_id: 'exec-1',
          step_id: 'step-1',
          step_number: 1,
          stage_name: 'Investment Casting',
          execution_type: 'normal',
          attempt_number: 1,
          execution_status: 'completed',
          latest_qc_result: 'PASS',
          latest_defect_severity: 'NONE',
          total_checks: 1,
          has_passed: true,
        },
      ],
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockQcSummary);

    const res = await productionExecutionService.getOrderQualitySummary('order-101');

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/orders/order-101/quality-checks');
    expect(res.quality_gate_passed).toBe(true);
    expect(res.passed).toBe(3);
  });

  it('completes order when quality gate passes', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      order_id: 'order-101',
      status: 'completed',
      message: 'Production order marked as completed.',
    });

    const res = await productionExecutionService.completeOrder('order-101');

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production/orders/order-101/complete',
      {}
    );
    expect(res.status).toBe('completed');
  });

  // ---------------------------------------------------------------------------
  // 8. Workshop Roster & Equipment Retrieval
  // ---------------------------------------------------------------------------
  it('retrieves available workshop workers for assignment', async () => {
    const mockWorkers: WorkerListResponse = {
      items: [
        {
          id: 'worker-1',
          user_id: 'user-1',
          name: 'Jean Goldsmith',
          skill: 'Casting Specialist',
          is_available: true,
          capacity_hours_per_day: 8,
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
        },
        {
          id: 'worker-2',
          user_id: 'user-1',
          name: 'Maya StoneSetter',
          skill: 'Stone Setter',
          is_available: true,
          capacity_hours_per_day: 8,
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
        },
      ],
      total: 2,
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockWorkers);

    const res = await productionService.getWorkers();

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/workers');
    expect(res.items).toHaveLength(2);
    expect(res.items[0].skill).toBe('Casting Specialist');
  });

  it('retrieves available workshop machines for assignment', async () => {
    const mockMachines: MachineListResponse = {
      items: [
        {
          id: 'machine-1',
          user_id: 'user-1',
          name: 'Indutherm VC400',
          machine_type: 'Vacuum Casting Machine',
          is_available: true,
          capacity_hours_per_day: 12,
          created_at: '2026-10-01T00:00:00Z',
          updated_at: '2026-10-01T00:00:00Z',
        },
      ],
      total: 1,
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockMachines);

    const res = await productionService.getMachines();

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/machines');
    expect(res.items).toHaveLength(1);
    expect(res.items[0].machine_type).toBe('Vacuum Casting Machine');
  });

  // ---------------------------------------------------------------------------
  // 9. Dashboard Production Orders Loading
  // ---------------------------------------------------------------------------
  it('retrieves active production orders for workshop dashboard table', async () => {
    const mockOrdersList: ProductionOrderListResponse = {
      items: [mockOrder],
      total: 1,
      page: 1,
      page_size: 50,
      pages: 1,
    };

    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockOrdersList);

    const res = await productionService.getOrders({ page_size: 50 });

    expect(getSpy).toHaveBeenCalledWith('/api/v1/production/orders', {
      params: { page_size: 50 },
    });
    expect(res.items).toHaveLength(1);
    expect(res.items[0].id).toBe('order-101');
  });
});
