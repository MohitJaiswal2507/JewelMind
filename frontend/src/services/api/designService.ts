/**
 * Jewellery Design API Client Service
 */

import apiClient from './client';
import {
  Design,
  DesignCreateInput,
  DesignFilters,
  DesignListResponse,
  DesignUpdateInput,
} from '../../types/design';

export class DesignService {
  /**
   * Retrieves paginated list of designs for authenticated user.
   */
  public async getDesigns(filters?: DesignFilters): Promise<DesignListResponse> {
    const params: Record<string, string | number | boolean | undefined> = {};

    if (filters?.category) {
      params.category = filters.category;
    }
    if (filters?.status) {
      params.status = filters.status;
    }
    if (filters?.search && filters.search.trim()) {
      params.search = filters.search.trim();
    }
    if (filters?.page) {
      params.page = filters.page;
    }
    if (filters?.page_size) {
      params.page_size = filters.page_size;
    }

    return apiClient.get<DesignListResponse>('/api/v1/designs', { params });
  }

  /**
   * Retrieves single design by ID.
   */
  public async getDesign(id: string): Promise<Design> {
    return apiClient.get<Design>(`/api/v1/designs/${id}`);
  }

  /**
   * Creates a new jewellery design.
   */
  public async createDesign(data: DesignCreateInput): Promise<Design> {
    return apiClient.post<Design>('/api/v1/designs', data);
  }

  /**
   * Updates an existing design.
   */
  public async updateDesign(id: string, data: DesignUpdateInput): Promise<Design> {
    return apiClient.patch<Design>(`/api/v1/designs/${id}`, data);
  }

  /**
   * Deletes a design by ID.
   */
  public async deleteDesign(id: string): Promise<{ success: boolean; message: string; design_id: string }> {
    return apiClient.delete<{ success: boolean; message: string; design_id: string }>(`/api/v1/designs/${id}`);
  }
}

export const designService = new DesignService();
export default designService;
