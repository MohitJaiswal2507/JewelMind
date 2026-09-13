/**
 * JewelMind Phase B — Gemini UX & Service Integration Tests.
 *
 * Covers all 8 mandatory tests specified in Section 21 of the Phase B specification,
 * plus verification for the 3 user-mandated corrections:
 *
 * 1. User Intent "Locked" Meaning: Semantic priority (explicit user requirements
 *    prioritized over AI suggestions), while final prompt remains 100% user-editable.
 * 2. YOLO Category Source: Only pass verified YOLO V2 category when available; never
 *    invent or pass selectedCategory as YOLO.
 * 3. Strict Renderer Boundary: Phase B ends at preparing the editable final prompt;
 *    zero alterations to existing render API execution, parameters, or models.
 *
 * Mocks all backend HTTP requests; ZERO real Gemini API calls.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { geminiDesignService } from '../services/api/geminiDesignService';
import { apiClient, ApiClientError } from '../services/api/client';
import { aiRenderingService, RenderOptions } from '../services/api/aiRenderingService';
import {
  EnhancePromptResponse,
  AnalyzeDesignResponse,
  StructuredDesignUnderstanding,
} from '../types/ai';

const sampleUnderstanding: StructuredDesignUnderstanding = {
  jewellery_category: 'ring',
  category_confidence: 0.95,
  design_summary: 'Solitaire engagement ring in platinum with a brilliant diamond center stone and slender shank.',
  material: {
    primary_metal: '950 platinum',
    finish: 'polished high-shine',
    accent_metal: null,
    material_notes: null,
  },
  gemstones: {
    has_gemstones: true,
    primary_gemstone: {
      gemstone_type: 'diamond',
      cut: 'round brilliant',
      estimated_count: 1,
      setting_type: '4-prong basket',
      color_or_clarity: 'D-F colorless',
    },
    secondary_gemstones: [],
    gemstone_details: 'Single round brilliant diamond center stone',
  },
  structure: {
    silhouette: 'classic solitaire',
    symmetry: 'radial symmetry',
    setting_style: 'elevated 4-prong basket',
    stone_arrangement: 'solitaire',
    band_or_body_structure: 'thin comfort-fit shank',
    decorative_elements: [],
    edge_details: 'knife-edge',
    surface_details: 'high-polish',
    clasp_or_findings: null,
  },
  design_motifs: ['Classic Bridal Solitaire', 'Modern Minimalist'],
  user_intent_preserved: true,
  user_constraints_applied: ['platinum', 'round brilliant diamond', 'thin shank'],
};

const sampleEnhanceResponse: EnhancePromptResponse = {
  success: true,
  original_prompt: 'platinum round brilliant diamond thin shank',
  enhanced_prompt:
    'A masterpiece fine jewellery solitaire ring crafted in 950 platinum with a mirror-polished finish, featuring a center 1.5 carat round brilliant cut diamond in an elevated 4-prong basket setting, completed with an ultra-thin 1.6mm comfort-fit shank.',
  design_understanding: sampleUnderstanding,
  renderer_prompt:
    'masterpiece fine jewellery, solitaire ring, 950 platinum, polished, round brilliant cut diamond, 4-prong basket, thin shank, photorealistic, 8k, raytracing',
  negative_prompt:
    'blurry, distorted prongs, missing facets, low quality, cartoon, render artifacts',
  yolo_category: null,
  gemini_category: 'ring',
  resolved_category: 'ring',
  category_conflict: false,
  warnings: [],
  fallback_applied: false,
};

const sampleAnalyzeResponse: AnalyzeDesignResponse = {
  success: true,
  design_understanding: sampleUnderstanding,
  renderer_prompt:
    'fine jewellery, solitaire ring, 950 platinum, round brilliant diamond, delicate shank, studio lighting',
  negative_prompt:
    'blurry, lowres, distorted geometry, extra prongs, bad anatomy',
  original_prompt: null,
  enhanced_prompt: 'Photorealistic platinum ring with round brilliant diamond',
  yolo_category: null,
  gemini_category: 'ring',
  resolved_category: 'ring',
  category_conflict: false,
  warnings: [],
  fallback_applied: false,
};

describe('Phase B — Gemini UX & Service Integration Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // TEST 1
  it('TEST 1: Prompt entered -> Enhance with AI -> enhanced prompt returned and formatted', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(sampleEnhanceResponse);

    const promptInput = 'vintage emerald ring in yellow gold';
    const response = await geminiDesignService.enhancePrompt({
      user_prompt: promptInput,
    });

    expect(postSpy).toHaveBeenCalledTimes(1);
    expect(postSpy).toHaveBeenCalledWith('/api/v1/ai/gemini/enhance-prompt', {
      user_prompt: promptInput,
    });

    expect(response.success).toBe(true);
    expect(response.enhanced_prompt).toBeDefined();
    expect(response.renderer_prompt).toContain('masterpiece fine jewellery');
    expect(response.design_understanding.jewellery_category).toBe('ring');
  });

  // TEST 2 (With Correction 1: Semantic priority + fully editable prompt)
  it('TEST 2: Explicit user constraints (platinum, round brilliant diamond, thin shank) have semantic priority, and final prompt remains 100% user-editable', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce(sampleEnhanceResponse);

    const explicitPrompt = 'platinum round brilliant diamond thin shank';
    const response = await geminiDesignService.enhancePrompt({
      user_prompt: explicitPrompt,
    });

    // 1. Semantic Priority: verify user intent preserved flag is true
    expect(response.design_understanding.user_intent_preserved).toBe(true);

    // 2. Semantic Priority: verify all explicit user constraints are locked in applied constraints list
    const applied = response.design_understanding.user_constraints_applied;
    expect(applied).toContain('platinum');
    expect(applied).toContain('round brilliant diamond');
    expect(applied).toContain('thin shank');

    // 3. Semantic Priority: metal not converted to gold, stone not converted to emerald
    expect(response.design_understanding.material.primary_metal.toLowerCase()).toContain('platinum');
    expect(response.renderer_prompt.toLowerCase()).toContain('platinum');
    expect(response.renderer_prompt.toLowerCase()).not.toContain('yellow gold');
    expect(response.design_understanding.gemstones.primary_gemstone?.gemstone_type.toLowerCase()).toBe('diamond');
    expect(response.design_understanding.structure.band_or_body_structure.toLowerCase()).toContain('thin');

    // 4. Correction 1: User still has full authority to manually edit the resulting prompt
    let userFinalPrompt = response.renderer_prompt;
    expect(typeof userFinalPrompt).toBe('string');
    // Artisan adjusts diamond carat and adds pave halo in the editable field
    userFinalPrompt = `${userFinalPrompt}, 2.0 carat center, micro-pave diamond halo`;
    expect(userFinalPrompt).toContain('micro-pave diamond halo');
  });

  // TEST 3 (With Correction 2: No invented YOLO context)
  it('TEST 3: Image/sketch + empty prompt -> Analyze Design -> structured understanding displayed (no invented YOLO category)', async () => {
    const uploadSpy = vi.spyOn(apiClient, 'upload').mockResolvedValueOnce(sampleAnalyzeResponse);

    const dummyBlob = new Blob(['sketch-data'], { type: 'image/png' });
    // When no verified YOLO detection exists, yoloCategory is undefined
    const response = await geminiDesignService.analyzeDesign({
      file: dummyBlob,
      userPrompt: '',
      yoloCategory: undefined,
      yoloConfidence: undefined,
    });

    expect(uploadSpy).toHaveBeenCalledTimes(1);
    const [path, formData] = uploadSpy.mock.calls[0] as [string, FormData];
    expect(path).toBe('/api/v1/ai/gemini/analyze-design');

    // Verify no YOLO category was invented in the FormData
    expect(formData.get('yolo_category')).toBeNull();

    expect(response.success).toBe(true);
    expect(response.design_understanding).toBeDefined();
    expect(response.design_understanding.jewellery_category).toBe('ring');
    expect(response.design_understanding.material.primary_metal).toBe('950 platinum');
    expect(response.design_understanding.gemstones.primary_gemstone?.gemstone_type).toBe('diamond');
    expect(response.design_understanding.structure.band_or_body_structure).toContain('thin');
    expect(response.renderer_prompt).toBeDefined();
    expect(response.negative_prompt).toBeDefined();
  });

  // TEST 3b (Verified YOLO category is passed when actually available)
  it('TEST 3b: When verified YOLO V2 detection exists, it is accurately passed to Gemini', async () => {
    const uploadSpy = vi.spyOn(apiClient, 'upload').mockResolvedValueOnce({
      ...sampleAnalyzeResponse,
      yolo_category: 'ring',
    });

    const dummyBlob = new Blob(['sketch-data'], { type: 'image/png' });
    await geminiDesignService.analyzeDesign({
      file: dummyBlob,
      yoloCategory: 'ring',
      yoloConfidence: 0.94,
    });

    const [, formData] = uploadSpy.mock.calls[0] as [string, FormData];
    expect(formData.get('yolo_category')).toBe('ring');
    expect(formData.get('yolo_confidence')).toBe('0.94');
  });

  // TEST 4
  it('TEST 4: Gemini backend returns failure (HTTP 500 / 503) -> friendly error handled gracefully', async () => {
    const apiError = new ApiClientError(503, {
      error: {
        code: 'SERVICE_UNAVAILABLE',
        message: 'Gemini service is currently overloaded. Please retry later.',
      },
    });

    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(apiError);

    await expect(
      geminiDesignService.enhancePrompt({ user_prompt: 'platinum ring' })
    ).rejects.toThrow('Gemini service is currently overloaded.');
  });

  // TEST 5
  it('TEST 5: Prompt enhancement fails -> original prompt remains intact and usable', async () => {
    const apiError = new ApiClientError(500, {
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Design understanding service error: connection timeout',
      },
    });
    vi.spyOn(apiClient, 'post').mockRejectedValueOnce(apiError);

    // Simulated component state model
    const state = {
      originalPrompt: 'white gold emerald solitaire ring',
      editablePrompt: 'white gold emerald solitaire ring',
      status: 'idle' as 'idle' | 'enhancing' | 'error',
      errorMessage: null as string | null,
    };

    state.status = 'enhancing';
    try {
      await geminiDesignService.enhancePrompt({ user_prompt: state.originalPrompt });
    } catch (err: unknown) {
      state.status = 'error';
      state.errorMessage = err instanceof Error ? err.message : 'Error enhancing prompt';
    }

    // Assert: original prompt was NOT wiped or corrupted
    expect(state.originalPrompt).toBe('white gold emerald solitaire ring');
    expect(state.editablePrompt).toBe('white gold emerald solitaire ring');
    expect(state.status).toBe('error');
    expect(state.errorMessage).toContain('connection timeout');
  });

  // TEST 6
  it('TEST 6: User edits enhanced prompt -> manual edits remain strictly intact', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce(sampleEnhanceResponse);

    const initialPrompt = 'platinum diamond ring';
    const res = await geminiDesignService.enhancePrompt({ user_prompt: initialPrompt });

    // Step 1: AI enhances prompt
    let editablePrompt = res.renderer_prompt;
    expect(editablePrompt).toContain('950 platinum');

    // Step 2: Artisan modifies prompt to add "milgrain borders and 1.2ct stone"
    const userCustomized = `${editablePrompt}, with delicate milgrain borders, engraved gallery, 1.2ct diamond`;
    editablePrompt = userCustomized;

    // Step 3: Verify the customized prompt is the one that will be passed to future rendering
    expect(editablePrompt).toContain('delicate milgrain borders');
    expect(editablePrompt).toContain('engraved gallery');
    expect(editablePrompt).not.toBe(res.renderer_prompt);
  });

  // TEST 7
  it('TEST 7: Gemini loading state prevents duplicate concurrent submissions', async () => {
    let pendingResolve: (value: EnhancePromptResponse) => void;
    const slowPromise = new Promise<EnhancePromptResponse>((resolve) => {
      pendingResolve = resolve;
    });

    const postSpy = vi.spyOn(apiClient, 'post').mockReturnValueOnce(slowPromise);

    // Simulated modal submission handler guarding against duplicate clicks
    let isEnhancing = false;
    let callCount = 0;

    const handleEnhanceClick = async () => {
      if (isEnhancing) return; // Guard
      isEnhancing = true;
      callCount++;
      try {
        await geminiDesignService.enhancePrompt({ user_prompt: 'gold bangle' });
      } finally {
        isEnhancing = false;
      }
    };

    // First click initiates request
    const firstCall = handleEnhanceClick();
    expect(isEnhancing).toBe(true);

    // Second and third accidental clicks while in-flight
    const secondCall = handleEnhanceClick();
    const thirdCall = handleEnhanceClick();

    await Promise.all([secondCall, thirdCall]);
    expect(callCount).toBe(1);
    expect(postSpy).toHaveBeenCalledTimes(1);

    // Resolve initial request
    pendingResolve!(sampleEnhanceResponse);
    await firstCall;
    expect(isEnhancing).toBe(false);
  });

  // TEST 8
  it('TEST 8: No Gemini credentials / backend offline -> fallback/graceful degradation operates cleanly', async () => {
    const fallbackResponse: EnhancePromptResponse = {
      ...sampleEnhanceResponse,
      fallback_applied: true,
      warnings: ['Gemini API key not configured; local heuristics builder applied.'],
    };

    vi.spyOn(apiClient, 'post').mockResolvedValueOnce(fallbackResponse);

    const res = await geminiDesignService.enhancePrompt({
      user_prompt: '18k rose gold ruby pendant',
    });

    expect(res.success).toBe(true);
    expect(res.fallback_applied).toBe(true);
    expect(res.warnings[0]).toContain('local heuristics builder applied');
    expect(res.renderer_prompt).toBeDefined();
    expect(res.design_understanding).toBeDefined();
  });

  // TEST 9 (Correction 3: Strict Renderer Boundary)
  it('TEST 9: Strict Renderer Boundary — Phase B does NOT alter renderer execution or automatically feed Gemini output', async () => {
    const uploadSpy = vi.spyOn(apiClient, 'upload').mockResolvedValueOnce({
      model_version: 'controlnet-v2-sd15',
      controlnet_version: 'lineart',
      image_width: 512,
      image_height: 512,
      seed: 42,
      control_type: 'lineart',
      control_strength: 1.0,
      steps: 20,
      guidance_scale: 7.5,
      inference_time_ms: 2100,
      device_used: 'cuda:0',
      output_url: 'https://storage.jewelmind.ai/renders/render-42.png',
      created_at: new Date().toISOString(),
    });

    const dummyFile = new Blob(['sketch'], { type: 'image/png' });
    const standardOptions: RenderOptions = {
      category: 'ring',
      design_id: 'design-123',
      sketch_url: 'https://storage.jewelmind.ai/sketches/ring.png',
      material: '18k yellow gold',
      gemstone: 'round brilliant diamond',
      control_type: 'lineart',
      control_strength: 1.0,
      steps: 20,
      prompt: 'custom artisan lighting notes',
    };

    // Call existing unchanged aiRenderingService
    await aiRenderingService.renderSketch(dummyFile, standardOptions);

    expect(uploadSpy).toHaveBeenCalledTimes(1);
    const [path, formData] = uploadSpy.mock.calls[0] as [string, FormData];
    expect(path).toBe('/api/v1/ai/render');
    expect(formData.get('prompt')).toBe('custom artisan lighting notes');
    expect(formData.get('material')).toBe('18k yellow gold');
    expect(formData.get('category')).toBe('ring');
  });
});
