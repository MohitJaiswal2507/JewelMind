/**
 * Standard API Interfaces & Contracts for JewelMind Client
 */

export interface ErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiError {
  error: ErrorDetail;
  request_id?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  request_id?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  database_configured: boolean;
}

export interface DatabaseHealthResponse {
  status: string;
  database: string;
  detail?: string;
}
