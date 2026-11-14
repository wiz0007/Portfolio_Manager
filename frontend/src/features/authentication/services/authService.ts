import { apiClient } from '@/services/api/client';
import {
  User,
  RegisterRequest,
  LoginRequest,
  AuthResponse,
} from '../types/auth';

export const authService = {
  async register(payload: RegisterRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/register/', payload);
  },

  async login(payload: LoginRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/login/', payload);
  },

  async googleLogin(credential: string): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/google/', { credential });
  },

  async logout(): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/logout/');
  },

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me/');
  },

  async updateProfile(payload: { full_name: string }): Promise<User> {
    return apiClient.patch<User>('/users/me/', payload);
  },

  async verifyEmail(payload: { token: string }): Promise<{ message: string; status: string }> {
    return apiClient.post<{ message: string; status: string }>('/auth/verify-email/', payload);
  },

  async resendVerification(payload?: { email?: string }): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/auth/resend-verification/', payload || {});
  },
};

