import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';
import { DashboardOverview } from '../types/dashboard';
import { ApiClientError } from '@/services/api/client';

export const DASHBOARD_OVERVIEW_QUERY_KEY = ['dashboardOverview'];

export function useDashboardOverview() {
  return useQuery<DashboardOverview, ApiClientError>({
    queryKey: DASHBOARD_OVERVIEW_QUERY_KEY,
    queryFn: () => dashboardService.getOverview(),
    staleTime: 60 * 1000,
  });
}
