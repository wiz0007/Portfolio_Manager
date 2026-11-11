import { useQuery } from '@tanstack/react-query';
import { healthService, HealthCheckResponse } from '@/services/api/healthService';

export function useHealthCheck() {
  return useQuery<HealthCheckResponse>({
    queryKey: ['systemHealth'],
    queryFn: () => healthService.checkHealth(),
    staleTime: 60 * 1000, // cache for 1 minute to avoid excessive polling
    refetchOnWindowFocus: false,
    retry: 1,
  });
}
