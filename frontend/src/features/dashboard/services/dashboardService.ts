import { apiClient } from '@/services/api/client';
import { DashboardOverview } from '../types/dashboard';

export const dashboardService = {
  async getOverview(): Promise<DashboardOverview> {
    return apiClient.get<DashboardOverview>('/dashboard/overview/');
  },
};
