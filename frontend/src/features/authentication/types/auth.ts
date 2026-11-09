export interface User {
  id: string;
  email: string;
  full_name: string;
  date_joined: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  password_confirmation: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  message: string;
  user: User;
}

export interface ApiErrorResponse {
  detail?: string | string[];
  email?: string[];
  password?: string[];
  password_confirmation?: string[];
  full_name?: string[];
  [key: string]: unknown;
}
