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
