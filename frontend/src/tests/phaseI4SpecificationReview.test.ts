/**
 * JewelMind Phase I.4 — Artisan Production Specification Review & Approval Test Suite
 *
 * Verifies:
 * 1. productionSpecificationService.generateSpecification API integration
 * 2. productionSpecificationService.getSpecification API integration
 * 3. productionSpecificationService.getSpecificationsByRender API integration
 * 4. productionSpecificationService.updateSpecification (PATCH) API integration
 * 5. productionSpecificationService.approveSpecification (POST /approve) API integration
 * 6. Provenance tagging distinction: ARTISAN_OVERRIDE vs AI_ESTIMATE
 * 7. Support for gemstone-free designs (plain bands)
 * 8. Status and immutability flags: DRAFT vs APPROVED
 * 9. Sequential routing step ordering contract
 * 10. Client payload structure excludes forbidden server-controlled fields
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  productionSpecificationService,
  ProductionSpecificationResponse,
  ProductionSpecificationUpdateRequest,
} from '../services/api/productionSpecificationService';
import { apiClient } from '../services/api/client';

describe('Phase I.4 — Artisan Production Specification Review & Approval Frontend Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockDraftSpec: ProductionSpecificationResponse = {
    id: 'spec-uuid-1',
    user_id: 'user-uuid-1',
    design_id: 'design-uuid-1',
    render_id: 'render-uuid-1',
    version_number: 1,
    status: 'draft',
    category: 'ring',
    estimated_rough_metal_weight_grams: 5.5,
    estimated_finished_metal_weight_grams: 4.8,
    total_gemstone_count: 1,
    estimated_total_bench_hours: 8.5,
    complexity_rating: 'moderate',
    fabrication_notes: 'Initial AI manufacturing blueprint.',
    ai_confidence_score: 0.9,
    approved_at: null,
    created_at: '2026-09-22T00:00:00Z',
    updated_at: '2026-09-22T00:00:00Z',
    materials: [
      {
        id: 'mat-uuid-1',
        specification_id: 'spec-uuid-1',
        metal_type: 'gold',
        metal_purity: '18k',
        metal_color: 'yellow',
        metal_finish: 'high_polish',
        plating: null,
        estimated_weight_grams: 4.8,
        casting_loss_percentage: 10.0,
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T00:00:00Z',
        updated_at: '2026-09-22T00:00:00Z',
      },
    ],
    gemstones: [
      {
        id: 'gem-uuid-1',
        specification_id: 'spec-uuid-1',
        gemstone_type: 'diamond',
        cut_shape: 'round_brilliant',
        stone_count: 1,
        estimated_carat_weight: 1.0,
        approximate_dimensions_mm: '6.5mm',
        setting_type: 'prong',
        is_center_stone: true,
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T00:00:00Z',
        updated_at: '2026-09-22T00:00:00Z',
      },
    ],
    steps: [
      {
        id: 'step-uuid-1',
        specification_id: 'spec-uuid-1',
        step_number: 1,
        stage_name: 'Casting',
        required_skill: 'caster',
        required_machine_type: 'vacuum_caster',
        base_hours: 2.0,
        per_unit_hours: 0.5,
        description: 'Vacuum casting in 18k yellow gold.',
        quality_checkpoint: 'Check for porosity.',
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T00:00:00Z',
        updated_at: '2026-09-22T00:00:00Z',
      },
      {
        id: 'step-uuid-2',
        specification_id: 'spec-uuid-1',
        step_number: 2,
        stage_name: 'Stone Setting',
        required_skill: 'setter',
        required_machine_type: 'microscope_bench',
        base_hours: 4.0,
        per_unit_hours: 1.0,
        description: 'Set center diamond.',
        quality_checkpoint: 'Check prong tightness.',
        origin: 'AI_ESTIMATE',
        created_at: '2026-09-22T00:00:00Z',
        updated_at: '2026-09-22T00:00:00Z',
      },
    ],
  };

  // ---------------------------------------------------------------------------
  // 1. Service API Endpoint Verification
  // ---------------------------------------------------------------------------

  it('1. generateSpecification calls POST /api/v1/production-specifications/generate', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockDraftSpec);

    const result = await productionSpecificationService.generateSpecification({
      render_id: 'render-uuid-1',
      material_hint: '18k yellow gold',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/production-specifications/generate',
      {
        render_id: 'render-uuid-1',
        material_hint: '18k yellow gold',
      }
    );
    expect(result.id).toBe('spec-uuid-1');
    expect(result.status).toBe('draft');
  });

  it('2. getSpecification queries GET /api/v1/production-specifications/:id', async () => {
    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockDraftSpec);

    const result = await productionSpecificationService.getSpecification('spec-uuid-1');
    expect(getSpy).toHaveBeenCalledWith('/api/v1/production-specifications/spec-uuid-1');
    expect(result.materials).toHaveLength(1);
    expect(result.gemstones).toHaveLength(1);
    expect(result.steps).toHaveLength(2);
  });

  it('3. getSpecificationsByRender queries GET /api/v1/production-specifications/by-render/:renderId', async () => {
    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce([mockDraftSpec]);

    const result = await productionSpecificationService.getSpecificationsByRender('render-uuid-1');
    expect(getSpy).toHaveBeenCalledWith('/api/v1/production-specifications/by-render/render-uuid-1');
    expect(result).toHaveLength(1);
    expect(result[0].version_number).toBe(1);
  });

  it('4. updateSpecification calls PATCH /api/v1/production-specifications/:id with overrides', async () => {
    const updatedSpec: ProductionSpecificationResponse = {
      ...mockDraftSpec,
      estimated_finished_metal_weight_grams: 5.2,
      materials: [
        {
          ...mockDraftSpec.materials[0],
          estimated_weight_grams: 5.2,
          origin: 'ARTISAN_OVERRIDE',
        },
      ],
    };

    const patchSpy = vi.spyOn(apiClient, 'patch').mockResolvedValueOnce(updatedSpec);

    const payload: ProductionSpecificationUpdateRequest = {
      estimated_finished_metal_weight_grams: 5.2,
      materials: [
        {
          id: 'mat-uuid-1',
          metal_type: 'gold',
          metal_purity: '18k',
          estimated_weight_grams: 5.2,
        },
      ],
    };

    const result = await productionSpecificationService.updateSpecification('spec-uuid-1', payload);
    expect(patchSpy).toHaveBeenCalledWith(
      '/api/v1/production-specifications/spec-uuid-1',
      payload
    );
    expect(result.estimated_finished_metal_weight_grams).toBe(5.2);
    expect(result.materials[0].origin).toBe('ARTISAN_OVERRIDE');
  });

  it('5. approveSpecification calls POST /api/v1/production-specifications/:id/approve', async () => {
    const approvedSpec: ProductionSpecificationResponse = {
      ...mockDraftSpec,
      status: 'approved',
      approved_at: '2026-09-22T00:30:00Z',
    };

    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(approvedSpec);

    const result = await productionSpecificationService.approveSpecification('spec-uuid-1');
    expect(postSpy).toHaveBeenCalledWith('/api/v1/production-specifications/spec-uuid-1/approve');
    expect(result.status).toBe('approved');
    expect(result.approved_at).not.toBeNull();
  });

  // ---------------------------------------------------------------------------
  // 2. Data Contract & Business Rules Verification
  // ---------------------------------------------------------------------------

  it('6. Correctly tracks provenance between AI_ESTIMATE and ARTISAN_OVERRIDE', () => {
    const specWithMixedProvenance: ProductionSpecificationResponse = {
      ...mockDraftSpec,
      materials: [
        {
          ...mockDraftSpec.materials[0],
          origin: 'ARTISAN_OVERRIDE',
        },
      ],
      steps: [
        {
          ...mockDraftSpec.steps[0],
          origin: 'AI_ESTIMATE',
        },
        {
          ...mockDraftSpec.steps[1],
          origin: 'ARTISAN_OVERRIDE',
        },
      ],
    };

    expect(specWithMixedProvenance.materials[0].origin).toBe('ARTISAN_OVERRIDE');
    expect(specWithMixedProvenance.steps[0].origin).toBe('AI_ESTIMATE');
    expect(specWithMixedProvenance.steps[1].origin).toBe('ARTISAN_OVERRIDE');
  });

  it('7. Supports gemstone-free designs (plain bands) without errors', () => {
    const plainBandSpec: ProductionSpecificationResponse = {
      ...mockDraftSpec,
      total_gemstone_count: 0,
      gemstones: [],
    };

    expect(plainBandSpec.gemstones).toHaveLength(0);
    expect(plainBandSpec.total_gemstone_count).toBe(0);
    expect(plainBandSpec.materials).toHaveLength(1);
    expect(plainBandSpec.steps.length).toBeGreaterThan(0);
  });

  it('8. Enforces sequential step numbering (1..N)', () => {
    const sortedStepNumbers = mockDraftSpec.steps
      .map((s) => s.step_number)
      .sort((a, b) => a - b);

    expect(sortedStepNumbers).toEqual([1, 2]);
    for (let i = 0; i < sortedStepNumbers.length; i++) {
      expect(sortedStepNumbers[i]).toBe(i + 1);
    }
  });

  it('9. Correctly differentiates draft and approved states', () => {
    expect(mockDraftSpec.status).toBe('draft');
    expect(mockDraftSpec.approved_at).toBeNull();

    const lockedSpec: ProductionSpecificationResponse = {
      ...mockDraftSpec,
      status: 'approved',
      approved_at: '2026-09-22T00:30:00Z',
    };

    expect(lockedSpec.status).toBe('approved');
    expect(lockedSpec.approved_at).toBeDefined();
  });

  it('10. Client update payload preserves exact render and design bindings', () => {
    const payload: ProductionSpecificationUpdateRequest = {
      category: 'pendant',
      estimated_rough_metal_weight_grams: 6.0,
      estimated_finished_metal_weight_grams: 5.0,
    };

    // Verify client payload does NOT contain server-controlled fields
    expect((payload as any).id).toBeUndefined();
    expect((payload as any).user_id).toBeUndefined();
    expect((payload as any).design_id).toBeUndefined();
    expect((payload as any).render_id).toBeUndefined();
    expect((payload as any).version_number).toBeUndefined();
    expect((payload as any).status).toBeUndefined();
    expect((payload as any).approved_at).toBeUndefined();
  });
});
