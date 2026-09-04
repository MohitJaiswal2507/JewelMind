/**
 * Typed client service for JewelMind AI Generative Rendering API.
 */

import { apiClient } from './client';

export interface RenderResultResponse {
  model_version: string;
  controlnet_version: string;
  image_width: number;
  image_height: number;
  seed: number;
  control_type: string;
  control_strength: number;
  steps: number;
  guidance_scale: number;
  inference_time_ms: number;
  device_used: string;
  output_url: string;
  created_at: string;
  conditioning_metadata?: {
    original_size: [number, number];
    processed_size: [number, number];
    control_type: string;
    padding: [number, number, number, number];
    edge_density?: number;
  };
}

export interface RenderOptions {
  category?: 'ring' | 'earring' | 'pendant' | 'necklace' | 'bracelet' | 'bangle' | 'brooch' | 'other' | string;
  design_id?: string;
  prompt?: string;
  negative_prompt?: string;
  material?: string;
  gemstone?: string;
  control_type?: 'lineart' | 'canny';
  control_strength?: number;
  steps?: number;
  guidance_scale?: number;
  seed?: number;
  width?: number;
  height?: number;
}

export const aiRenderingService = {
  /**
   * Send sketch file and conditioning parameters to AI rendering endpoint.
   */
  async renderSketch(
    file: File | Blob,
    options: RenderOptions = {}
  ): Promise<RenderResultResponse> {
    const formData = new FormData();
    formData.append('file', file, 'sketch.png');

    if (options.category) formData.append('category', options.category);
    if (options.design_id) formData.append('design_id', options.design_id);
    if (options.prompt) formData.append('prompt', options.prompt);
    if (options.negative_prompt) formData.append('negative_prompt', options.negative_prompt);
    if (options.material) formData.append('material', options.material);
    if (options.gemstone) formData.append('gemstone', options.gemstone);
    if (options.control_type) formData.append('control_type', options.control_type);
    if (options.control_strength !== undefined) {
      formData.append('control_strength', String(options.control_strength));
    }
    if (options.steps !== undefined) formData.append('steps', String(options.steps));
    if (options.guidance_scale !== undefined) {
      formData.append('guidance_scale', String(options.guidance_scale));
    }
    if (options.seed !== undefined && options.seed !== null) {
      formData.append('seed', String(options.seed));
    }
    if (options.width !== undefined) formData.append('width', String(options.width));
    if (options.height !== undefined) formData.append('height', String(options.height));

    return apiClient.upload<RenderResultResponse>('/api/v1/ai/render', formData);
  },
};
