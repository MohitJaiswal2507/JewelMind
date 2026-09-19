/**
 * Centralized Typed API Client for JewelMind
 * Automatically injects authorization bearer tokens and correlation headers.
 */

import { ApiError } from '../../types/api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TOKEN_STORAGE_KEY = 'jewelmind_auth_token';

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  requiresAuth?: boolean;
}

export class ApiClientError extends Error {
  public code: string;
  public status: number;
  public details?: unknown;
  public requestId?: string;

  constructor(status: number, errorData: ApiError) {
    super(errorData.error.message || 'API request failed');
    this.name = 'ApiClientError';
    this.status = status;
    this.code = errorData.error.code || 'UNKNOWN_ERROR';
    this.details = errorData.error.details;
    this.requestId = errorData.request_id;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  public getToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  }

  public setToken(token: string): void {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }

  public clearToken(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const url = new URL(`${this.baseUrl}${cleanPath}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, requiresAuth = true, ...restOptions } = options;
    const url = this.buildUrl(path, params);

    const defaultHeaders: Record<string, string> = {
      Accept: 'application/json',
    };

    // Only set Content-Type to JSON if body is not FormData
    if (!(restOptions.body instanceof FormData)) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    const token = this.getToken();
    if (requiresAuth && token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...restOptions,
      headers: {
        ...defaultHeaders,
        ...headers,
      },
    });

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      let validationMessage: string | undefined;
      const rawDetails = data?.error?.details || data?.detail;
      if (Array.isArray(rawDetails) && rawDetails.length > 0) {
        validationMessage = rawDetails
          .map((item: any) => {
            if (typeof item === 'string') return item;
            const field = Array.isArray(item?.loc)
              ? item.loc.filter((l: any) => l !== 'body').join('.')
              : '';
            return field ? `${field}: ${item?.msg || 'Invalid value'}` : item?.msg || 'Validation error';
          })
          .join('; ');
      }

      const errorPayload: ApiError = {
        error: {
          code: data?.error?.code || (data?.detail?.error as string) || `HTTP_${response.status}`,
          message:
            validationMessage ||
            data?.error?.message ||
            (typeof data?.detail === 'string' ? data.detail : data?.detail?.message) ||
            response.statusText ||
            'An unexpected error occurred.',
          details: rawDetails,
        },
        request_id: data?.request_id || response.headers.get('X-Request-ID') || undefined,
      };

      throw new ApiClientError(response.status, errorPayload);
    }

    return data as T;
  }

  public get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' });
  }

  public post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public upload<T>(path: string, formData: FormData, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: formData,
    });
  }

  public put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(BASE_URL);
export default apiClient;
