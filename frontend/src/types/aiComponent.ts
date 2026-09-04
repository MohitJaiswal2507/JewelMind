/**
 * YOLO Component Detection Types for JewelMind Phase 13.
 */

export interface ComponentDetection {
  class_id: number;
  class_name: string;
  confidence: float;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  mask?: [number, number][]; // [[x, y], ...]
  normalized_mask?: [number, number][];
  area?: number;
}

export interface DetectionResult {
  model_version: string;
  image_size: [number, number]; // [width, height]
  inference_time_ms: number;
  device_used: string;
  detections: ComponentDetection[];
  total_detections: number;
}

export type float = number;
