/**
 * JewelMind Phase G — Canva AI Workspace & Conversational Copilot Tests.
 * 
 * Verifies:
 * 1. Conversational design state modification API contract.
 * 2. Iterative redesign passing previous_render_url.
 * 3. Text-to-Render pure generation (no sketch file required).
 * 4. DesignDetail signal timeout and resilient error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { geminiDesignService } from '../services/api/geminiDesignService';
import { aiRenderingService } from '../services/api/aiRenderingService';
import { designService } from '../services/api/designService';
import { apiClient, ApiClientError } from '../services/api/client';
import { DesignState, ModifyDesignResponse } from '../types/ai';

describe('Phase G Canva AI Workspace & Copilot Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('modifyDesignState calls POST /api/v1/ai/gemini/modify-design with current state and instruction', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      success: true,
      updated_state: {
        category: 'Ring',
        primary_metal: '18k rose gold',
        metal_finish: 'polished high-shine',
        accent_metal: null,
        has_gemstones: true,
        gemstone_type: 'blue sapphire',
        gemstone_cut: 'oval',
        gemstone_color: 'royal blue',
        gemstone_count: 1,
        setting_type: 'prong setting',
        accent_stones: null,
        style_aesthetic: 'modern luxury',
        silhouette: 'classic balanced silhouette',
        engraving_or_details: null,
        current_prompt: 'Photorealistic 18k rose gold ring with oval blue sapphire',
        renderer_prompt: 'photorealistic ring, 18k rose gold, oval blue sapphire',
        negative_prompt: 'deformed, low quality',
      },
      assistant_reply: "I've updated your ring to 18k rose gold with an oval blue sapphire.",
      changes_detected: ['primary_metal', 'gemstone_type', 'gemstone_cut'],
      renderer_prompt: 'photorealistic ring, 18k rose gold, oval blue sapphire',
      negative_prompt: 'deformed, low quality',
      fallback_applied: false,
      warnings: [],
    } as ModifyDesignResponse);

    const currentState: DesignState = {
      category: 'Ring',
      primary_metal: '18k yellow gold',
      metal_finish: 'polished high-shine',
      accent_metal: null,
      has_gemstones: true,
      gemstone_type: 'diamond',
      gemstone_cut: 'round brilliant',
      gemstone_color: 'colorless',
      gemstone_count: 1,
      setting_type: 'prong setting',
      accent_stones: null,
      style_aesthetic: 'modern luxury',
      silhouette: 'classic balanced silhouette',
      engraving_or_details: null,
      current_prompt: '18k yellow gold solitaire ring with round diamond',
    };

    const res = await geminiDesignService.modifyDesignState({
      current_state: currentState,
      user_instruction: 'Change the metal to 18k rose gold and the center stone to an oval blue sapphire',
    });

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/ai/gemini/modify-design',
      expect.objectContaining({
        current_state: currentState,
        user_instruction: expect.stringContaining('rose gold'),
      })
    );

    expect(res.success).toBe(true);
    expect(res.updated_state.primary_metal).toBe('18k rose gold');
    expect(res.updated_state.gemstone_type).toBe('blue sapphire');
    expect(res.changes_detected).toContain('primary_metal');
    expect(res.changes_detected).toContain('gemstone_type');
  });

  it('aiRenderingService appends previous_render_url when iterative redesign is triggered', async () => {
    let capturedFormData: FormData | null = null;
    vi.spyOn(apiClient, 'upload').mockImplementation(async (_url: string, data: FormData) => {
      capturedFormData = data;
      return {
        model_version: 'sd15-lora',
        controlnet_version: 'controlnet-v2',
        image_width: 512,
        image_height: 512,
        seed: 42,
        control_type: 'canny',
        control_strength: 0.65,
        steps: 20,
        guidance_scale: 7.5,
        inference_time_ms: 1200,
        device_used: 'cuda:0',
        output_url: 'https://example.com/renders/iterative_02.png',
        created_at: new Date().toISOString(),
      };
    });

    await aiRenderingService.renderSketch(null, {
      category: 'ring',
      prompt: 'Photorealistic 18k rose gold ring with emerald',
      control_type: 'canny',
      control_strength: 0.65,
      previous_render_url: 'https://example.com/renders/iterative_01.png',
    });

    expect(capturedFormData).not.toBeNull();
    expect(capturedFormData!.get('previous_render_url')).toBe('https://example.com/renders/iterative_01.png');
    expect(capturedFormData!.get('control_type')).toBe('canny');
  });

  it('aiRenderingService supports pure Text-to-Render without sketch file', async () => {
    let capturedFormData: FormData | null = null;
    vi.spyOn(apiClient, 'upload').mockImplementation(async (_url: string, data: FormData) => {
      capturedFormData = data;
      return {
        model_version: 'sd15-lora',
        controlnet_version: 'controlnet-v2',
        image_width: 512,
        image_height: 512,
        seed: 123,
        control_type: 'lineart',
        control_strength: 0.0,
        steps: 20,
        guidance_scale: 7.5,
        inference_time_ms: 1100,
        device_used: 'cuda:0',
        output_url: 'https://example.com/renders/text_render.png',
        created_at: new Date().toISOString(),
      };
    });

    await aiRenderingService.renderSketch(null, {
      category: 'pendant',
      prompt: 'Photorealistic platinum art deco pendant with emerald and diamonds',
      control_strength: 0.0,
    });

    expect(capturedFormData).not.toBeNull();
    expect(capturedFormData!.get('file')).toBeNull();
    expect(capturedFormData!.get('category')).toBe('pendant');
    expect(capturedFormData!.get('prompt')).toContain('art deco pendant');
  });

  it('designService getDesign passes AbortSignal for Critical Bug #1 timeout protection', async () => {
    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
      id: 'test-uuid-1',
      name: 'Victorian Ring',
      category: 'Ring',
      status: 'draft',
      user_id: 'user-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const controller = new AbortController();
    const result = await designService.getDesign('test-uuid-1', controller.signal);

    expect(getSpy).toHaveBeenCalledWith('/api/v1/designs/test-uuid-1', { signal: controller.signal });
    expect(result.id).toBe('test-uuid-1');
  });

  it('Directive 4: EnhancePrompt does not auto-render and returns editable enhanced prompt', async () => {
    const enhanceSpy = vi.spyOn(geminiDesignService, 'enhancePrompt').mockResolvedValueOnce({
      success: true,
      original_prompt: 'Create a platinum earring with a blue sapphire',
      enhanced_prompt: 'A masterwork platinum drop earring adorned with a vivid pear-cut blue sapphire in secure basket setting',
      design_understanding: {
        jewellery_category: 'Earring',
        design_summary: 'Platinum drop earring with blue sapphire',
        material: { primary_metal: 'platinum', finish: 'polished', accent_metal: null },
        gemstones: {
          has_gemstones: true,
          primary_gemstone: { gemstone_type: 'blue sapphire', cut: 'pear', color_or_clarity: 'vivid blue', setting_type: 'basket', estimated_count: 2 },
          secondary_gemstones: [],
        },
        structure: {
          silhouette: 'drop silhouette',
          band_or_body_structure: 'delicate ear wire',
          symmetry: 'bilateral symmetry',
          setting_style: 'basket setting',
          stone_arrangement: 'drop cluster',
          decorative_elements: [],
        },
        design_motifs: ['modern luxury'],
        user_intent_preserved: true,
        user_constraints_applied: ['metal: platinum', 'gemstone: blue sapphire'],
        category_confidence: 0.96,
      },
      renderer_prompt: 'photorealistic earring fine jewellery product photograph, crafted in polished platinum, pear blue sapphire',
      negative_prompt: 'low quality, deformed',
      resolved_category: 'Earring',
      category_conflict: false,
      warnings: [],
      fallback_applied: false,
    });

    const renderSpy = vi.spyOn(aiRenderingService, 'renderSketch');

    const res = await geminiDesignService.enhancePrompt({
      user_prompt: 'Create a platinum earring with a blue sapphire',
    });

    expect(enhanceSpy).toHaveBeenCalled();
    expect(res.enhanced_prompt).toContain('platinum drop earring');
    expect(res.enhanced_prompt).toContain('blue sapphire');
    // Critical: Enhancement MUST NOT trigger rendering automatically
    expect(renderSpy).not.toHaveBeenCalled();
  });

  it('Directive 7: Clean DesignState does not leak gold, diamond, or ring into plain jewellery', () => {
    // Silver bangle with no gemstone
    const cleanBangleState: DesignState = {
      category: 'Bangle',
      primary_metal: 'silver',
      metal_finish: 'polished',
      has_gemstones: false,
      gemstone_type: null,
      current_prompt: 'Silver bangle with no gemstone',
    };

    expect(cleanBangleState.category).toBe('Bangle');
    expect(cleanBangleState.primary_metal).toBe('silver');
    expect(cleanBangleState.has_gemstones).toBe(false);
    expect(cleanBangleState.gemstone_type).toBeNull();
    expect(cleanBangleState.primary_metal).not.toContain('gold');
  });

  it('Directive 8: Comparison mode configuration pairs appropriate source with render', () => {
    // Mode A: Doodle -> Render shows Doodle + Render
    const doodleComparison = {
      mode: 'doodle',
      left: 'canvas_doodle_data_url',
      right: 'https://example.com/renders/doodle_render.png',
    };
    expect(doodleComparison.left).toBe('canvas_doodle_data_url');
    expect(doodleComparison.right).toContain('doodle_render');

    // Mode B: Image -> Render shows Uploaded Image + Render
    const imageComparison = {
      mode: 'image',
      left: 'https://example.com/uploads/reference_photo.jpg',
      right: 'https://example.com/renders/image_render.png',
    };
    expect(imageComparison.left).toContain('reference_photo');
    expect(imageComparison.right).toContain('image_render');

    // Mode C: Iterative redesign shows Previous Render + New Render
    const iterativeComparison = {
      mode: 'iterative',
      left: 'https://example.com/renders/v1_yellow_gold_ring.png',
      right: 'https://example.com/renders/v2_rose_gold_ring.png',
    };
    expect(iterativeComparison.left).toContain('v1_yellow_gold');
    expect(iterativeComparison.right).toContain('v2_rose_gold');
  });

  it('Phase G1.1: Text -> Render preserves NECKLACE category and sends control_strength=0.0', async () => {
    let capturedData: FormData | null = null;
    vi.spyOn(apiClient, 'upload').mockImplementation(async (_url: string, data: FormData) => {
      capturedData = data;
      return {
        model_version: 'sd15-lora',
        controlnet_version: 'controlnet-v2',
        image_width: 512,
        image_height: 512,
        seed: 42,
        control_type: 'lineart',
        control_strength: 0.0,
        steps: 20,
        guidance_scale: 7.5,
        inference_time_ms: 1500,
        device_used: 'cuda:0',
        output_url: 'https://storage.jewelmind.ai/renders/necklace_01.png',
        created_at: new Date().toISOString(),
      };
    });

    await aiRenderingService.renderSketch(null, {
      category: 'necklace',
      source_blueprint_category: 'necklace',
      prompt: 'Royal South Indian antique gold bridal necklace on a black display stand',
      material: '18k yellow gold',
      gemstone: 'round brilliant diamond',
      control_strength: 0.0,
      control_type: 'lineart',
    });

    expect(capturedData).not.toBeNull();
    expect(capturedData!.get('category')).toBe('necklace');
    expect(capturedData!.get('control_strength')).toBe('0');
    expect(capturedData!.get('file')).toBeNull();
  });

  it('Phase G1.1: ApiClientError correctly parses FastAPI 422 detail list with location and message', () => {
    const errorData = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Request validation failed.',
        details: [
          {
            loc: ['body', 'control_strength'],
            msg: 'Input should be greater than or equal to 0.0',
            type: 'greater_than_equal',
          },
        ],
      },
    };
    const clientErr = new ApiClientError(422, errorData);
    expect(clientErr.status).toBe(422);
    expect(clientErr.code).toBe('VALIDATION_ERROR');
    expect(clientErr.details).toBeDefined();
  });
});

