/**
 * Authentication Service
 */

import { apiClient } from './client';
import { AuthResponse, LoginCredentials, RegisterData, User } from '../../types/auth';

export const authService = {
  /**
   * Register a new user account
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data, {
      requiresAuth: false,
    });
    if (response?.access_token) {
      apiClient.setToken(response.access_token);
    }
    return response;
  },

  /**
   * Log in user and save token
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', credentials, {
      requiresAuth: false,
    });
    if (response?.access_token) {
      apiClient.setToken(response.access_token);
    }
    return response;
  },

  /**
   * Fetch current authenticated user profile
   */
  async getMe(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me');
  },

  /**
   * Log out user and clear client token
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout', {});
    } catch {
      // Ignore network errors on logout
    } finally {
      apiClient.clearToken();
    }
  },

  /**
   * Check if token exists locally
   */
  hasToken(): boolean {
    return !!apiClient.getToken();
  },
};

export default authService;
