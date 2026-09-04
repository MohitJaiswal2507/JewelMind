/**
 * Typed client service for JewelMind YOLO Component Detection API.
 */

import { apiClient } from './client';
import { DetectionResult } from '../../types/aiComponent';

export interface ComponentDetectionOptions {
  conf?: number;
}

export const aiComponentService = {
  /**
   * Send sketch file/blob to the YOLO component detection endpoint.
   */
  async detectComponents(
    file: File | Blob,
    options: ComponentDetectionOptions = {}
  ): Promise<DetectionResult> {
    const formData = new FormData();
    formData.append('file', file, 'sketch.png');

    const params: Record<string, string | number> = {};
    if (options.conf !== undefined) {
      params.conf = options.conf;
    }

    return apiClient.upload<DetectionResult>('/api/v1/ai/components/detect', formData, {
      params,
    });
  },
};

export default aiComponentService;
