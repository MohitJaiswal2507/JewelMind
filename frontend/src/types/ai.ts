/**
 * JewelMind AI & Gemini Multimodal Design Understanding TypeScript Types.
 * Matches backend Pydantic schemas in backend/app/schemas/ai.py.
 */

export type JewelleryCategory =
  | 'ring'
  | 'earring'
  | 'pendant'
  | 'necklace'
  | 'bracelet'
  | 'bangle'
  | 'brooch'
  | 'other_jewellery';

export interface MaterialSpec {
  primary_metal: string;
  finish: string;
  accent_metal?: string | null;
  material_notes?: string | null;
}

export interface GemstoneItem {
  gemstone_type: string;
  cut: string;
  estimated_count: number;
  setting_type: string;
  color_or_clarity?: string | null;
}

export interface GemstoneSpec {
  has_gemstones: boolean;
  primary_gemstone?: GemstoneItem | null;
  secondary_gemstones: GemstoneItem[];
  gemstone_details?: string | null;
}

export interface StructuralSpec {
  silhouette: string;
  symmetry: string;
  setting_style: string;
  stone_arrangement: string;
  band_or_body_structure: string;
  decorative_elements: string[];
  edge_details?: string | null;
  surface_details?: string | null;
  clasp_or_findings?: string | null;
}

export interface StructuredDesignUnderstanding {
  jewellery_category: string;
  category_confidence?: number | null;
  design_summary: string;
  material: MaterialSpec;
  gemstones: GemstoneSpec;
  structure: StructuralSpec;
  design_motifs: string[];
  user_intent_preserved: boolean;
  user_constraints_applied: string[];
}

export interface YoloGroundingContext {
  detected_category: string;
  confidence: number;
  bounding_box?: number[] | null;
}

export interface AnalyzeDesignOptions {
  file?: File | Blob | null;
  imageUrl?: string;
  imageBase64?: string;
  userPrompt?: string;
  yoloCategory?: string;
  yoloConfidence?: number;
}

export interface AnalyzeDesignResponse {
  success: boolean;
  design_understanding: StructuredDesignUnderstanding;
  renderer_prompt: string;
  negative_prompt: string;
  original_prompt?: string | null;
  enhanced_prompt?: string | null;
  yolo_category?: string | null;
  gemini_category?: string | null;
  resolved_category: string;
  category_conflict: boolean;
  warnings: string[];
  fallback_applied: boolean;
}

export interface EnhancePromptRequest {
  user_prompt: string;
  image_base64?: string | null;
  image_url?: string | null;
  yolo_category?: string | null;
  yolo_confidence?: number | null;
}

export interface EnhancePromptResponse {
  success: boolean;
  original_prompt: string;
  enhanced_prompt: string;
  design_understanding: StructuredDesignUnderstanding;
  renderer_prompt: string;
  negative_prompt: string;
  yolo_category?: string | null;
  gemini_category?: string | null;
  resolved_category: string;
  category_conflict: boolean;
  warnings: string[];
  fallback_applied: boolean;
}

export type GeminiStatus = 'idle' | 'analyzing' | 'enhancing' | 'success' | 'error';
