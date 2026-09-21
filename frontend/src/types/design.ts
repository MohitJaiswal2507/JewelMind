/**
 * Jewellery Design TypeScript Types & Constants
 */

export type DesignCategory =
  | 'Ring'
  | 'Necklace'
  | 'Earrings'
  | 'Bracelet'
  | 'Bangle'
  | 'Pendant'
  | 'Brooch'
  | 'Other';

export const DESIGN_CATEGORIES: DesignCategory[] = [
  'Ring',
  'Necklace',
  'Earrings',
  'Bracelet',
  'Bangle',
  'Pendant',
  'Brooch',
  'Other',
];

export type DesignStatus =
  | 'draft'
  | 'ready'
  | 'rendering'
  | 'rendered'
  | 'archived';

export const DESIGN_STATUSES: { label: string; value: DesignStatus }[] = [
  { label: 'Draft', value: 'draft' },
  { label: 'Ready for Review', value: 'ready' },
  { label: 'Rendering (AI)', value: 'rendering' },
  { label: 'Rendered', value: 'rendered' },
  { label: 'Archived', value: 'archived' },
];

export interface Design {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  category: DesignCategory;
  status: DesignStatus;
  sketch_image_url: string | null;
  rendered_image_url: string | null;
  ai_prompt: string | null;
  created_at: string;
  updated_at: string;
  renders?: DesignRender[];
}

export interface DesignCreateInput {
  name: string;
  description?: string | null;
  category: DesignCategory;
  status?: DesignStatus;
  sketch_image_url?: string | null;
  rendered_image_url?: string | null;
  ai_prompt?: string | null;
}

export interface DesignUpdateInput {
  name?: string;
  description?: string | null;
  category?: DesignCategory;
  status?: DesignStatus;
  sketch_image_url?: string | null;
  rendered_image_url?: string | null;
  ai_prompt?: string | null;
}

export interface DesignFilters {
  category?: DesignCategory | '';
  status?: DesignStatus | '';
  search?: string;
  page?: number;
  page_size?: number;
}

export interface DesignListResponse {
  items: Design[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DesignRender {
  id: string;
  design_id: string;
  user_id: string;
  version_number: number;
  parent_render_id: string | null;
  render_mode: string;
  prompt: string;
  enhanced_prompt: string | null;
  structured_state: Record<string, any> | null;
  image_url: string;
  thumbnail_url: string | null;
  control_type: string;
  control_strength: number;
  seed: number | null;
  is_approved_for_production: boolean;
  created_at: string;
}

export interface DesignRenderListResponse {
  renders: DesignRender[];
  total: number;
}

