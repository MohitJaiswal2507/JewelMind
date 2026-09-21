/**
 * Production Specification API Service (Phase I.4)
 * Handles client-side communication for AI generation, artisan review/override,
 * and manufacturing approval of Production Specifications.
 */

import { apiClient } from './client';

export interface ProductionMaterialResponse {
  id: string;
  specification_id: string;
  metal_type: string;
  metal_purity: string;
  metal_color?: string | null;
  metal_finish?: string | null;
  plating?: string | null;
  estimated_weight_grams?: number | null;
  casting_loss_percentage?: number | null;
  origin: 'AI_ESTIMATE' | 'ARTISAN_OVERRIDE' | string;
  created_at: string;
  updated_at: string;
}

export interface ProductionGemstoneResponse {
  id: string;
  specification_id: string;
  gemstone_type: string;
  cut_shape?: string | null;
  stone_count: number;
  estimated_carat_weight?: number | null;
  approximate_dimensions_mm?: string | null;
  setting_type?: string | null;
  is_center_stone: boolean;
  origin: 'AI_ESTIMATE' | 'ARTISAN_OVERRIDE' | string;
  created_at: string;
  updated_at: string;
}

export interface ProductionStepResponse {
  id: string;
  specification_id: string;
  step_number: number;
  stage_name: string;
  required_skill: string;
  required_machine_type?: string | null;
  base_hours: number;
  per_unit_hours: number;
  description?: string | null;
  quality_checkpoint?: string | null;
  origin: 'AI_ESTIMATE' | 'ARTISAN_OVERRIDE' | string;
  created_at: string;
  updated_at: string;
}

export interface ProductionSpecificationResponse {
  id: string;
  user_id: string;
  design_id: string;
  render_id: string;
  version_number: number;
  status: 'draft' | 'approved' | 'archived' | string;
  category: string;
  estimated_rough_metal_weight_grams?: number | null;
  estimated_finished_metal_weight_grams?: number | null;
  total_gemstone_count: number;
  estimated_total_bench_hours?: number | null;
  complexity_rating?: 'simple' | 'moderate' | 'intricate' | 'masterpiece' | string | null;
  fabrication_notes?: string | null;
  ai_confidence_score?: number | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
  materials: ProductionMaterialResponse[];
  gemstones: ProductionGemstoneResponse[];
  steps: ProductionStepResponse[];
}

export interface ProductionMaterialUpdate {
  id?: string | null;
  metal_type: string;
  metal_purity: string;
  metal_color?: string | null;
  metal_finish?: string | null;
  plating?: string | null;
  estimated_weight_grams?: number | null;
  casting_loss_percentage?: number | null;
}

export interface ProductionGemstoneUpdate {
  id?: string | null;
  gemstone_type: string;
  cut_shape?: string | null;
  stone_count: number;
  estimated_carat_weight?: number | null;
  approximate_dimensions_mm?: string | null;
  setting_type?: string | null;
  is_center_stone: boolean;
}

export interface ProductionStepUpdate {
  id?: string | null;
  step_number: number;
  stage_name: string;
  required_skill: string;
  required_machine_type?: string | null;
  base_hours: number;
  per_unit_hours: number;
  description?: string | null;
  quality_checkpoint?: string | null;
}

export interface ProductionSpecificationUpdateRequest {
  category?: string;
  estimated_rough_metal_weight_grams?: number | null;
  estimated_finished_metal_weight_grams?: number | null;
  total_gemstone_count?: number;
  estimated_total_bench_hours?: number | null;
  complexity_rating?: 'simple' | 'moderate' | 'intricate' | 'masterpiece' | string | null;
  fabrication_notes?: string | null;
  materials?: ProductionMaterialUpdate[];
  gemstones?: ProductionGemstoneUpdate[];
  steps?: ProductionStepUpdate[];
}

export interface ProductionSpecificationGenerateRequest {
  render_id: string;
  user_prompt?: string | null;
  material_hint?: string | null;
  gemstone_hint?: string | null;
}

class ProductionSpecificationService {
  /**
   * Generates a new Production Specification from an approved render.
   */
  async generateSpecification(
    req: ProductionSpecificationGenerateRequest
  ): Promise<ProductionSpecificationResponse> {
    return apiClient.post<ProductionSpecificationResponse>(
      '/api/v1/production-specifications/generate',
      req
    );
  }

  /**
   * Retrieves a single specification by its ID.
   */
  async getSpecification(specificationId: string): Promise<ProductionSpecificationResponse> {
    return apiClient.get<ProductionSpecificationResponse>(
      `/api/v1/production-specifications/${specificationId}`
    );
  }

  /**
   * Retrieves all specification versions bound to a specific render.
   */
  async getSpecificationsByRender(renderId: string): Promise<ProductionSpecificationResponse[]> {
    return apiClient.get<ProductionSpecificationResponse[]>(
      `/api/v1/production-specifications/by-render/${renderId}`
    );
  }

  /**
   * Updates a draft production specification with artisan overrides.
   */
  async updateSpecification(
    specificationId: string,
    req: ProductionSpecificationUpdateRequest
  ): Promise<ProductionSpecificationResponse> {
    return apiClient.patch<ProductionSpecificationResponse>(
      `/api/v1/production-specifications/${specificationId}`,
      req
    );
  }

  /**
   * Validates and locks a draft specification as APPROVED.
   */
  async approveSpecification(specificationId: string): Promise<ProductionSpecificationResponse> {
    return apiClient.post<ProductionSpecificationResponse>(
      `/api/v1/production-specifications/${specificationId}/approve`
    );
  }
}

export const productionSpecificationService = new ProductionSpecificationService();
export default productionSpecificationService;
