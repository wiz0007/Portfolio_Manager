import { apiClient } from './client';

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  database: 'connected' | 'unavailable';
}

export const healthService = {
  async checkHealth(): Promise<HealthCheckResponse> {
    return apiClient.get<HealthCheckResponse>('/health/');
  },
};
