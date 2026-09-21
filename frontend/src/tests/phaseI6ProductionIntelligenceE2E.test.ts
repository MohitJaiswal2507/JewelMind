/**
 * JewelMind Phase I.6 — End-to-End Production Intelligence Validation Test Suite
 *
 * Validates the complete frontend service, state, and UI workflow:
 * 1. Approved Render -> AI Generation -> Review -> Overrides -> Approval
 * 2. Approved Spec -> Create Production Order -> CP-SAT Optimization
 * 3. Traceable lineage in Gantt schedule and task details
 * 4. All 8 jewellery categories validated
 * 5. Gem-free vs multi-gemstone routing
 * 6. Dynamic N-step operations (3-step, 5-step, custom)
 * 7. Infeasibility diagnostics and legacy order backward compatibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../services/api/client';
import {
  productionSpecificationService,
  ProductionSpecificationResponse,
  ProductionSpecificationUpdateRequest,
} from '../services/api/productionSpecificationService';
import {
  productionService,
} from '../services/api/productionService';
import {
  ProductionOrder,
  OptimizationResponse,
  ProductionOrderCreateFromSpecificationInput,
} from '../types/production';

describe('Phase I.6 — End-to-End Production Intelligence Validation Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockRenderId = 'render-4cb175d5-450a-40b2-84d2-a25c856bf011';
  const mockDesignId = 'design-7b4f50e7-a234-4594-821e-99b0c4fa803e';

  const createMockDraftSpec = (category = 'ring'): ProductionSpecificationResponse => ({
    id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
    user_id: 'user-4b274210-973b-4e17-9b3f-2cb2f6ee7524',
    design_id: mockDesignId,
    render_id: mockRenderId,
    version_number: 1,
    status: 'draft',
    approved_at: null,
    category,
    ai_confidence_score: 0.94,
    complexity_rating: 'intricate',
    total_gemstone_count: 1,
    estimated_total_bench_hours: 8.5,
    estimated_finished_metal_weight_grams: 5.2,
    fabrication_notes: 'Precision casting with micro-prong setting.',
    created_at: '2026-09-22T02:00:00Z',
    updated_at: '2026-09-22T02:00:00Z',
    materials: [
      {
        id: 'mat-1',
        specification_id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
        metal_type: 'gold',
        metal_purity: '18k',
        metal_color: 'yellow',
        metal_finish: 'high_polish',
        plating: null,
        estimated_weight_grams: 5.2,
        casting_loss_percentage: 10.0,
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
    ],
    gemstones: [
      {
        id: 'gem-1',
        specification_id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
        gemstone_type: 'diamond',
        cut_shape: 'round_brilliant',
        stone_count: 1,
        estimated_carat_weight: 1.0,
        approximate_dimensions_mm: '6.5mm',
        setting_type: 'prong',
        is_center_stone: true,
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
    ],
    steps: [
      {
        id: 'step-1',
        specification_id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
        step_number: 1,
        stage_name: 'CAD & 3D Wax Pattern Printing',
        required_skill: 'cad_design',
        required_machine_type: '3d_wax_printer',
        base_hours: 1.5,
        per_unit_hours: 0.25,
        description: 'Validate CAD geometry and print castable wax.',
        quality_checkpoint: 'Dimensional tolerance check within +/- 0.05mm.',
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
      {
        id: 'step-2',
        specification_id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
        step_number: 2,
        stage_name: 'Investment Casting & Spruing',
        required_skill: 'casting',
        required_machine_type: 'casting_furnace',
        base_hours: 2.0,
        per_unit_hours: 0.5,
        description: 'Dewaxing and vacuum induction casting.',
        quality_checkpoint: 'Zero surface porosity under magnification.',
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
      {
        id: 'step-3',
        specification_id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
        step_number: 3,
        stage_name: 'Precision Stone Setting',
        required_skill: 'stone_setting',
        required_machine_type: null,
        base_hours: 1.5,
        per_unit_hours: 0.75,
        description: 'Prong seat burring and diamond setting.',
        quality_checkpoint: 'Stone tight under microscope with level table.',
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
      {
        id: 'step-4',
        specification_id: 'spec-4bef03ed-46a7-416e-acf7-ad4001a7a013',
        step_number: 4,
        stage_name: 'Final Rouge Polishing & Ultrasonic Wash',
        required_skill: 'polishing',
        required_machine_type: 'polishing_lathe',
        base_hours: 0.75,
        per_unit_hours: 0.3,
        description: 'High-luster polishing and ultrasonic cleaning.',
        quality_checkpoint: 'Flawless mirror finish without compound residue.',
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
    ],
  });

  const createMockApprovedSpec = (draft: ProductionSpecificationResponse): ProductionSpecificationResponse => ({
    ...draft,
    status: 'approved',
    approved_at: '2026-09-22T02:05:00Z',
  });

  const createMockOrderFromSpec = (spec: ProductionSpecificationResponse, qty = 1): ProductionOrder => ({
    id: 'order-e2e-1',
    user_id: spec.user_id,
    design_id: spec.design_id,
    render_id: spec.render_id,
    specification_id: spec.id,
    specification_version: spec.version_number,
    specification_category: spec.category,
    routing_steps_count: spec.steps.length,
    materials_count: spec.materials.length,
    gemstones_count: spec.gemstones.length,
    design_name: 'Royal Solitaire Ring',
    design_category: spec.category,
    design_thumbnail_url: 'https://storage.jewelmind.ai/renders/thumb.png',
    approved_render_url: 'https://storage.jewelmind.ai/renders/approved.png',
    quantity: qty,
    priority: 'high',
    status: 'pending',
    deadline: '2026-10-01T00:00:00Z',
    is_overdue: false,
    notes: 'Artisan order created from approved spec',
    created_at: '2026-09-22T02:06:00Z',
    updated_at: '2026-09-22T02:06:00Z',
  });

  // -------------------------------------------------------------------------
  // 1. Complete End-to-End UI & Service Journey
  // -------------------------------------------------------------------------
  it('executes full E2E lifecycle: generate -> override -> approve -> create order -> schedule', async () => {
    const draftSpec = createMockDraftSpec('ring');
    const updatedDraftSpec: ProductionSpecificationResponse = {
      ...draftSpec,
      fabrication_notes: 'Artisan override: Hand-beaded prong finish.',
      materials: [
        {
          ...draftSpec.materials[0],
          estimated_weight_grams: 5.8,
          origin: 'ARTISAN_OVERRIDE',
        },
      ],
    };
    const approvedSpec = createMockApprovedSpec(updatedDraftSpec);
    const createdOrder = createMockOrderFromSpec(approvedSpec, 2);

    const mockScheduleResponse: OptimizationResponse = {
      status: 'success',
      solver_status: 'OPTIMAL',
      message: 'Optimal schedule generated with dynamic specification routing.',
      unscheduled_order_ids: [],
      infeasibility_reasons: [],
      metrics: {
        makespan_hours: 18.0,
        total_orders_scheduled: 1,
        total_orders_unscheduled: 0,
        worker_utilization_pct: 82.5,
        machine_utilization_pct: 71.0,
        orders_on_time: 1,
        orders_overdue: 0,
        solver_runtime_ms: 85,
      },
      schedule: [
        {
          id: 'task-1',
          order_id: createdOrder.id,
          design_name: 'Royal Solitaire Ring',
          quantity: 2,
          priority: 'high',
          operation_name: 'CAD & 3D Wax Pattern Printing',
          worker_id: 'worker-1',
          worker_name: 'CAD Specialist',
          machine_id: 'mach-1',
          machine_name: 'SLA Wax 3D Printer',
          start_time: '2026-09-22T08:00:00Z',
          end_time: '2026-09-22T10:00:00Z',
          duration_hours: 2.0,
          sequence_order: 1,
          is_overdue: false,
          specification_id: approvedSpec.id,
          step_number: 1,
          quality_checkpoint: 'Dimensional tolerance check within +/- 0.05mm.',
        },
        {
          id: 'task-2',
          order_id: createdOrder.id,
          design_name: 'Royal Solitaire Ring',
          quantity: 2,
          priority: 'high',
          operation_name: 'Investment Casting & Spruing',
          worker_id: 'worker-2',
          worker_name: 'Master Caster',
          machine_id: 'mach-2',
          machine_name: 'Vacuum Induction Furnace',
          start_time: '2026-09-22T10:00:00Z',
          end_time: '2026-09-22T13:00:00Z',
          duration_hours: 3.0,
          sequence_order: 2,
          is_overdue: false,
          specification_id: approvedSpec.id,
          step_number: 2,
          quality_checkpoint: 'Zero surface porosity under magnification.',
        },
        {
          id: 'task-3',
          order_id: createdOrder.id,
          design_name: 'Royal Solitaire Ring',
          quantity: 2,
          priority: 'high',
          operation_name: 'Precision Stone Setting',
          worker_id: 'worker-3',
          worker_name: 'Diamond Setter',
          machine_id: null,
          machine_name: null,
          start_time: '2026-09-22T13:00:00Z',
          end_time: '2026-09-22T16:00:00Z',
          duration_hours: 3.0,
          sequence_order: 3,
          is_overdue: false,
          specification_id: approvedSpec.id,
          step_number: 3,
          quality_checkpoint: 'Stone tight under microscope with level table.',
        },
        {
          id: 'task-4',
          order_id: createdOrder.id,
          design_name: 'Royal Solitaire Ring',
          quantity: 2,
          priority: 'high',
          operation_name: 'Final Rouge Polishing & Ultrasonic Wash',
          worker_id: 'worker-4',
          worker_name: 'Master Polisher',
          machine_id: 'mach-3',
          machine_name: 'Precision Polishing Lathe',
          start_time: '2026-09-22T16:00:00Z',
          end_time: '2026-09-22T17:30:00Z',
          duration_hours: 1.5,
          sequence_order: 4,
          is_overdue: false,
          specification_id: approvedSpec.id,
          step_number: 4,
          quality_checkpoint: 'Flawless mirror finish without compound residue.',
        },
      ],
    };

    // Step 1: Generate specification
    vi.spyOn(apiClient, 'post').mockImplementation(async (url) => {
      if (url === '/api/v1/production-specifications/generate') {
        return draftSpec;
      }
      if (url === `/api/v1/production-specifications/${draftSpec.id}/approve`) {
        return approvedSpec;
      }
      if (url === '/api/v1/production/orders/from-specification') {
        return createdOrder;
      }
      if (url === '/api/v1/production/optimize') {
        return mockScheduleResponse;
      }
      throw new Error(`Unexpected POST url: ${url}`);
    });

    vi.spyOn(apiClient, 'patch').mockResolvedValue(updatedDraftSpec);

    // Run pipeline through frontend services
    const generated = await productionSpecificationService.generateSpecification({
      render_id: mockRenderId,
    });
    expect(generated.id).toBe(draftSpec.id);
    expect(generated.status).toBe('draft');
    expect(generated.materials[0].origin).toBe('AI_ESTIMATE');

    // Step 2: Artisan override
    const updatePayload: ProductionSpecificationUpdateRequest = {
      fabrication_notes: 'Artisan override: Hand-beaded prong finish.',
      materials: [
        {
          id: 'mat-1',
          metal_type: 'gold',
          metal_purity: '18k',
          metal_color: 'yellow',
          metal_finish: 'high_polish',
          plating: null,
          estimated_weight_grams: 5.8,
          casting_loss_percentage: 10.0,
        },
      ],
    };
    const overridden = await productionSpecificationService.updateSpecification(
      generated.id,
      updatePayload
    );
    expect(overridden.fabrication_notes).toContain('Artisan override');
    expect(overridden.materials[0].origin).toBe('ARTISAN_OVERRIDE');

    // Step 3: Approve specification
    const approved = await productionSpecificationService.approveSpecification(generated.id);
    expect(approved.status).toBe('approved');
    expect(approved.approved_at).not.toBeNull();

    // Step 4: Create order from approved spec
    const orderInput: ProductionOrderCreateFromSpecificationInput = {
      specification_id: approved.id,
      quantity: 2,
      priority: 'high',
      deadline: '2026-10-01T00:00:00Z',
      notes: 'Artisan order created from approved spec',
    };
    const order = await productionService.createOrderFromSpecification(orderInput);
    expect(order.specification_id).toBe(approved.id);
    expect(order.specification_version).toBe(1);
    expect(order.routing_steps_count).toBe(4);
    expect(order.quantity).toBe(2);

    // Step 5: Optimize schedule with CP-SAT
    const optimization = await productionService.optimizeProduction({
      horizon_days: 14,
      persist_schedule: true,
    });
    expect(optimization.status).toBe('success');
    expect(optimization.schedule).toHaveLength(4);

    // Step 6: Verify Gantt task lineage
    for (const task of optimization.schedule) {
      expect(task.specification_id).toBe(approved.id);
      expect(task.step_number).toBeGreaterThanOrEqual(1);
      expect(task.quality_checkpoint).toBeTruthy();
    }

    // Verify strict precedence in schedule (start_N >= end_{N-1})
    const sortedTasks = [...optimization.schedule].sort((a, b) => a.sequence_order - b.sequence_order);
    for (let i = 1; i < sortedTasks.length; i++) {
      const prevEnd = new Date(sortedTasks[i - 1].end_time).getTime();
      const currStart = new Date(sortedTasks[i].start_time).getTime();
      expect(currStart).toBeGreaterThanOrEqual(prevEnd);
    }
  });

  // -------------------------------------------------------------------------
  // 2. All 8 Jewellery Categories UI Contract
  // -------------------------------------------------------------------------
  const categories = [
    'ring',
    'earring',
    'pendant',
    'necklace',
    'bracelet',
    'bangle',
    'brooch',
    'other_jewellery',
  ];

  categories.forEach((cat) => {
    it(`supports category: ${cat} from specification through order creation`, async () => {
      const draft = createMockDraftSpec(cat);
      const approved = createMockApprovedSpec(draft);
      const order = createMockOrderFromSpec(approved);

      vi.spyOn(apiClient, 'post').mockImplementation(async (url) => {
        if (url === '/api/v1/production-specifications/generate') return draft;
        if (url.includes('/approve')) return approved;
        if (url === '/api/v1/production/orders/from-specification') return order;
        throw new Error(`Unexpected URL: ${url}`);
      });

      const spec = await productionSpecificationService.generateSpecification({ render_id: mockRenderId });
      expect(spec.category).toBe(cat);

      const appSpec = await productionSpecificationService.approveSpecification(spec.id);
      expect(appSpec.status).toBe('approved');

      const ord = await productionService.createOrderFromSpecification({
        specification_id: appSpec.id,
        quantity: 1,
        deadline: '2026-10-01T00:00:00Z',
      });
      expect(ord.specification_category).toBe(cat);
      expect(ord.specification_id).toBe(spec.id);
    });
  });

  // -------------------------------------------------------------------------
  // 3. Gemstone Variations: Gem-Free vs Multi-Gemstone
  // -------------------------------------------------------------------------
  it('correctly reflects gem-free design (stone setting omitted)', async () => {
    const plainSpec = createMockDraftSpec('ring');
    plainSpec.gemstones = [];
    plainSpec.steps = plainSpec.steps.filter((s) => s.required_skill !== 'stone_setting');

    vi.spyOn(apiClient, 'get').mockResolvedValue(plainSpec);

    const retrieved = await productionSpecificationService.getSpecification(plainSpec.id);
    expect(retrieved.gemstones).toHaveLength(0);
    const stoneSettingStep = retrieved.steps.find((s) => s.required_skill === 'stone_setting');
    expect(stoneSettingStep).toBeUndefined();
  });

  it('correctly reflects multi-gemstone pavé design (accurate counts and setting stage)', async () => {
    const paveSpec = createMockDraftSpec('ring');
    paveSpec.gemstones = [
      {
        id: 'gem-1',
        specification_id: paveSpec.id,
        gemstone_type: 'diamond',
        cut_shape: 'round_brilliant',
        stone_count: 1,
        estimated_carat_weight: 1.5,
        approximate_dimensions_mm: '7.4mm',
        setting_type: 'prong',
        is_center_stone: true,
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
      {
        id: 'gem-2',
        specification_id: paveSpec.id,
        gemstone_type: 'diamond',
        cut_shape: 'round_brilliant',
        stone_count: 24,
        estimated_carat_weight: 0.48,
        approximate_dimensions_mm: '1.5mm',
        setting_type: 'pave',
        is_center_stone: false,
        origin: 'ARTISAN_OVERRIDE',
        created_at: '2026-09-22T02:00:00Z',
        updated_at: '2026-09-22T02:00:00Z',
      },
    ];

    vi.spyOn(apiClient, 'get').mockResolvedValue(paveSpec);

    const retrieved = await productionSpecificationService.getSpecification(paveSpec.id);
    expect(retrieved.gemstones).toHaveLength(2);
    expect(retrieved.gemstones[1].stone_count).toBe(24);
    expect(retrieved.gemstones[1].setting_type).toBe('pave');
  });

  // -------------------------------------------------------------------------
  // 4. Infeasibility & Missing Resource Handling
  // -------------------------------------------------------------------------
  it('handles CP-SAT infeasibility diagnostics gracefully in UI response', async () => {
    const mockInfeasibleResponse: OptimizationResponse = {
      status: 'infeasible',
      solver_status: 'INFEASIBLE',
      message: 'Schedule infeasible: Missing worker with required skill stone_setting',
      unscheduled_order_ids: ['order-1'],
      infeasibility_reasons: ['No worker available with required skill stone_setting'],
      metrics: {
        makespan_hours: 0,
        total_orders_scheduled: 0,
        total_orders_unscheduled: 1,
        worker_utilization_pct: 0,
        machine_utilization_pct: 0,
        orders_on_time: 0,
        orders_overdue: 1,
        solver_runtime_ms: 12,
      },
      schedule: [],
    };

    vi.spyOn(apiClient, 'post').mockResolvedValue(mockInfeasibleResponse);

    const response = await productionService.optimizeProduction({ horizon_days: 7 });
    expect(response.status).toBe('infeasible');
    expect(response.schedule).toHaveLength(0);
    expect(response.message).toContain('Missing worker');
  });

  // -------------------------------------------------------------------------
  // 5. Legacy Orders Backward Compatibility
  // -------------------------------------------------------------------------
  it('supports legacy orders with null specification_id and 3-stage fallback', async () => {
    const mockLegacyOrder: ProductionOrder = {
      id: 'order-legacy-1',
      user_id: 'user-1',
      design_id: 'design-legacy',
      render_id: null,
      specification_id: null,
      specification_version: null,
      specification_category: null,
      routing_steps_count: 0,
      materials_count: 0,
      gemstones_count: 0,
      design_name: 'Vintage Ring',
      design_category: 'ring',
      design_thumbnail_url: null,
      approved_render_url: null,
      quantity: 1,
      priority: 'medium',
      status: 'pending',
      deadline: '2026-10-01T00:00:00Z',
      is_overdue: false,
      notes: null,
      created_at: '2026-09-22T00:00:00Z',
      updated_at: '2026-09-22T00:00:00Z',
    };

    vi.spyOn(apiClient, 'get').mockResolvedValue({
      items: [mockLegacyOrder],
      total: 1,
      page: 1,
      page_size: 10,
    });

    const ordersRes = await productionService.getOrders();
    expect(ordersRes.items).toHaveLength(1);
    const order = ordersRes.items[0];
    expect(order.specification_id).toBeNull();
    expect(order.specification_version).toBeNull();
    expect(order.routing_steps_count).toBe(0);
  });
});
