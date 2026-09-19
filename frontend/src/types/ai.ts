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

export type CategorySource = 'user_prompt' | 'user_selected' | 'yolo' | 'gemini' | 'default';

export interface AnalyzeDesignOptions {
  file?: File | Blob | null;
  imageUrl?: string;
  imageBase64?: string;
  userPrompt?: string;
  yoloCategory?: string;
  yoloConfidence?: number;
  sourceBlueprintCategory?: string;
  userSelectedCategory?: string;
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
  source_blueprint_category?: string | null;
  requested_category?: string | null;
  resolved_category: string;
  category_source?: CategorySource;
  category_conflict: boolean;
  category_conflict_reason?: string | null;
  warnings: string[];
  fallback_applied: boolean;
}

export interface EnhancePromptRequest {
  user_prompt: string;
  image_base64?: string | null;
  image_url?: string | null;
  yolo_category?: string | null;
  yolo_confidence?: number | null;
  source_blueprint_category?: string | null;
  user_selected_category?: string | null;
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
  source_blueprint_category?: string | null;
  requested_category?: string | null;
  resolved_category: string;
  category_source?: CategorySource;
  category_conflict: boolean;
  category_conflict_reason?: string | null;
  warnings: string[];
  fallback_applied: boolean;
}

export type GeminiStatus = 'idle' | 'analyzing' | 'enhancing' | 'modifying' | 'success' | 'error';

export interface DesignState {
  category?: string | null;
  primary_metal?: string | null;
  metal_finish?: string | null;
  accent_metal?: string | null;
  has_gemstones?: boolean | null;
  gemstone_type?: string | null;
  gemstone_cut?: string | null;
  gemstone_color?: string | null;
  gemstone_count?: number | null;
  setting_type?: string | null;
  accent_stones?: string | null;
  style_aesthetic?: string | null;
  silhouette?: string | null;
  engraving_or_details?: string | null;
  current_prompt: string;
  renderer_prompt?: string | null;
  negative_prompt?: string | null;
}

export interface ModifyDesignRequest {
  current_state: DesignState;
  user_instruction: string;
  image_base64?: string | null;
  image_url?: string | null;
}

export interface ModifyDesignResponse {
  success: boolean;
  updated_state: DesignState;
  assistant_reply: string;
  changes_detected: string[];
  renderer_prompt: string;
  negative_prompt: string;
  fallback_applied: boolean;
  warnings: string[];
}

