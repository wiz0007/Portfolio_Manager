import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { portfoliosApi } from '../api/portfoliosApi';
import {
  CreatePortfolioPayload,
  Portfolio,
  UpdatePortfolioPayload,
} from '../types';

export const PORTFOLIOS_QUERY_KEY = ['portfolios'];

export function usePortfolios() {
  return useQuery<Portfolio[]>({
    queryKey: PORTFOLIOS_QUERY_KEY,
    queryFn: () => portfoliosApi.getPortfolios(),
    staleTime: 30 * 1000,
  });
}

export function usePortfolio(id: string) {
  return useQuery<Portfolio>({
    queryKey: [...PORTFOLIOS_QUERY_KEY, id],
    queryFn: () => portfoliosApi.getPortfolio(id),
    enabled: Boolean(id),
  });
}

export function useCreatePortfolio() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreatePortfolioPayload) => portfoliosApi.createPortfolio(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PORTFOLIOS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['dashboardOverview'] });
    },
  });
}

export function useUpdatePortfolio() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdatePortfolioPayload }) =>
      portfoliosApi.updatePortfolio(id, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: PORTFOLIOS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: [...PORTFOLIOS_QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: ['dashboardOverview'] });
    },
  });
}

export function useDeletePortfolio() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => portfoliosApi.deletePortfolio(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PORTFOLIOS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['dashboardOverview'] });
    },
  });
}
