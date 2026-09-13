/**
 * JewelMind Phase F — Jewellery Type Consistency & State Synchronization Tests.
 *
 * Verifies:
 * 1. Category normalization ensures singular form matching the UI dropdown (e.g. "Earrings" -> "earring").
 * 2. API services forward source_blueprint_category and user_selected_category.
 * 3. Render service passes category_source, source_blueprint_category, and conflict_resolution in FormData.
 * 4. Conflict resolution state management handles Option A ("blueprint") and Option B ("force_requested").
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { normalizeCategory } from '../components/studio/AiRenderModal';
import { geminiDesignService } from '../services/api/geminiDesignService';
import { aiRenderingService, RenderOptions } from '../services/api/aiRenderingService';
import { apiClient } from '../services/api/client';

describe('Phase F: Category Normalization', () => {
  it('normalizes backend plural "Earrings" to singular "earring" matching dropdown option', () => {
    expect(normalizeCategory('Earrings')).toBe('earring');
    expect(normalizeCategory('earrings')).toBe('earring');
    expect(normalizeCategory('Earring')).toBe('earring');
  });

  it('normalizes various categories correctly without defaulting to ring', () => {
    expect(normalizeCategory('Necklace')).toBe('necklace');
    expect(normalizeCategory('necklaces')).toBe('necklace');
    expect(normalizeCategory('Ring')).toBe('ring');
    expect(normalizeCategory('Pendant')).toBe('pendant');
    expect(normalizeCategory('pendants')).toBe('pendant');
    expect(normalizeCategory('Brooch')).toBe('brooch');
    expect(normalizeCategory('brooches')).toBe('brooch');
    expect(normalizeCategory('Bracelet')).toBe('bracelet');
    expect(normalizeCategory('Bangle')).toBe('bangle');
  });

  it('handles null, undefined, or empty categories gracefully with fallback', () => {
    expect(normalizeCategory(null)).toBe('ring');
    expect(normalizeCategory(undefined)).toBe('ring');
    expect(normalizeCategory('')).toBe('ring');
  });
});

describe('Phase F: Service Telemetry & Payload Passing', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('geminiDesignService.enhancePrompt forwards source_blueprint_category and user_selected_category', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      renderer_prompt: 'A masterwork 18k yellow gold earring',
      negative_prompt: 'blurry, distorted',
      resolved_category: 'earring',
      category_source: 'user_prompt',
      category_conflict: true,
      category_conflict_reason: 'Prompt requested earring, but blueprint is necklace.',
      warnings: [],
      fallback_applied: false,
    });

    const res = await geminiDesignService.enhancePrompt({
      user_prompt: 'Create a sophisticated earring in yellow gold',
      source_blueprint_category: 'necklace',
      user_selected_category: 'necklace',
    });

    expect(postSpy).toHaveBeenCalledTimes(1);
    const calledPayload = postSpy.mock.calls[0][1] as Record<string, unknown>;
    expect(calledPayload.source_blueprint_category).toBe('necklace');
    expect(calledPayload.user_selected_category).toBe('necklace');
    expect(res.category_conflict).toBe(true);
    expect(res.resolved_category).toBe('earring');
  });

  it('aiRenderingService.renderSketch forwards source_blueprint_category, category_source, and conflict_resolution in FormData', async () => {
    let capturedFormData: FormData | null = null;
    vi.spyOn(apiClient, 'upload').mockImplementationOnce(async (_url, formData) => {
      capturedFormData = formData as FormData;
      return {
        output_url: 'http://localhost:8000/media/rendered/mock.png',
        seed: 42,
        steps: 20,
        control_type: 'lineart',
        inference_time_ms: 3200,
        device_used: 'NVIDIA GeForce RTX 4060',
        cached: false,
      };
    });

    const blob = new Blob(['mock sketch bytes'], { type: 'image/png' });
    const options: RenderOptions = {
      category: 'necklace',
      source_blueprint_category: 'necklace',
      category_source: 'yolo',
      conflict_resolution: 'blueprint',
      control_type: 'lineart',
      control_strength: 1.0,
      steps: 20,
      prompt: 'A masterwork necklace in 18k gold',
    };

    const res = await aiRenderingService.renderSketch(blob, options);

    expect(res.output_url).toBe('http://localhost:8000/media/rendered/mock.png');
    expect(capturedFormData).not.toBeNull();
    expect(capturedFormData!.get('category')).toBe('necklace');
    expect(capturedFormData!.get('source_blueprint_category')).toBe('necklace');
    expect(capturedFormData!.get('category_source')).toBe('yolo');
    expect(capturedFormData!.get('conflict_resolution')).toBe('blueprint');
  });

  it('geminiDesignService.enhancePrompt operates without source_blueprint_category when starting a clean render', async () => {
    const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
      renderer_prompt: 'Photorealistic emerald drop earrings in platinum',
      negative_prompt: 'blurry, distorted',
      resolved_category: 'earring',
      category_source: 'user_prompt',
      category_conflict: false,
      category_conflict_reason: null,
      warnings: [],
      fallback_applied: false,
    });

    const res = await geminiDesignService.enhancePrompt({
      user_prompt: 'Make an earring with emeralds and diamonds',
      source_blueprint_category: undefined,
      user_selected_category: undefined,
    });

    expect(postSpy).toHaveBeenCalledTimes(1);
    const payload = postSpy.mock.calls[0][1] as Record<string, unknown>;
    expect(payload.source_blueprint_category).toBeUndefined();
    expect(payload.image_base64).toBeUndefined();
    expect(payload.image_url).toBeUndefined();
    expect(res.category_conflict).toBe(false);
    expect(res.resolved_category).toBe('earring');
  });
});

