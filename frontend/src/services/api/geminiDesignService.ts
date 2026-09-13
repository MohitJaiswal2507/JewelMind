/**
 * Typed client service for JewelMind Gemini Multimodal Design Understanding & Prompt Enhancement.
 * Communicates strictly with backend proxy endpoints; no Gemini API keys are ever stored or exposed here.
 */

import { apiClient } from './client';
import {
  AnalyzeDesignOptions,
  AnalyzeDesignResponse,
  EnhancePromptRequest,
  EnhancePromptResponse,
} from '../../types/ai';

export const geminiDesignService = {
  /**
   * Analyze jewellery sketch or photograph with Gemini Vision.
   * Sends binary file, base64 data, or image URL along with optional prompt and YOLO context.
   */
  async analyzeDesign(options: AnalyzeDesignOptions = {}): Promise<AnalyzeDesignResponse> {
    const formData = new FormData();

    if (options.file) {
      formData.append('file', options.file, 'sketch.png');
    }
    if (options.imageUrl) {
      formData.append('image_url', options.imageUrl);
    }
    if (options.imageBase64) {
      formData.append('image_base64', options.imageBase64);
    }
    if (options.userPrompt) {
      formData.append('user_prompt', options.userPrompt);
    }
    if (options.yoloCategory) {
      formData.append('yolo_category', options.yoloCategory);
    }
    if (options.yoloConfidence !== undefined && options.yoloConfidence !== null) {
      formData.append('yolo_confidence', String(options.yoloConfidence));
    }
    if (options.sourceBlueprintCategory) {
      formData.append('source_blueprint_category', options.sourceBlueprintCategory);
    }
    if (options.userSelectedCategory) {
      formData.append('user_selected_category', options.userSelectedCategory);
    }

    return apiClient.upload<AnalyzeDesignResponse>('/api/v1/ai/gemini/analyze-design', formData);
  },

  /**
   * Enhance an artisan prompt with gemological terminology and diffusion anchors.
   * Strictly preserves explicit user intent (metal, gemstone, cut, shank profile).
   */
  async enhancePrompt(request: EnhancePromptRequest): Promise<EnhancePromptResponse> {
    return apiClient.post<EnhancePromptResponse>('/api/v1/ai/gemini/enhance-prompt', request);
  },
};

export default geminiDesignService;
