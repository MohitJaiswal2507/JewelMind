/**
 * Authentication Type Definitions
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  full_name: string;
  password: string;
}
