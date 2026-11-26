import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { investmentApi } from '../api/investmentApi';
import { useInvalidateDashboard } from '@/features/dashboard/hooks/useDashboard';
import {
  CreateInvestmentPayload,
  InvestmentDetailItem,
  InvestmentListItem,
  UpdateInvestmentPayload,
} from '../types/investmentApiTypes';

export const INVESTMENTS_QUERY_KEY = ['investments'];

export function useInvestments(portfolioId?: string, category?: string) {
  return useQuery<InvestmentListItem[]>({
    queryKey: [...INVESTMENTS_QUERY_KEY, { portfolioId, category }],
    queryFn: () => investmentApi.getInvestments(portfolioId, category),
    enabled: Boolean(portfolioId),
  });
}

export function useInvestment(portfolioId: string, id: string) {
  return useQuery<InvestmentDetailItem>({
    queryKey: [...INVESTMENTS_QUERY_KEY, portfolioId, id],
    queryFn: () => investmentApi.getInvestment(portfolioId, id),
    enabled: Boolean(portfolioId && id),
  });
}

export function useCreateInvestment() {
  const queryClient = useQueryClient();
  const invalidateDashboard = useInvalidateDashboard();

  return useMutation({
    mutationFn: (payload: CreateInvestmentPayload) => investmentApi.createInvestment(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: INVESTMENTS_QUERY_KEY });
      if (variables.portfolio) {
        queryClient.invalidateQueries({
          queryKey: [...INVESTMENTS_QUERY_KEY, { portfolioId: variables.portfolio }],
        });
      }
      invalidateDashboard();
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
}

export function useUpdateInvestment(portfolioId: string) {
  const queryClient = useQueryClient();
  const invalidateDashboard = useInvalidateDashboard();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateInvestmentPayload }) =>
      investmentApi.updateInvestment(portfolioId, id, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: INVESTMENTS_QUERY_KEY });
      queryClient.invalidateQueries({
        queryKey: [...INVESTMENTS_QUERY_KEY, portfolioId, variables.id],
      });
      invalidateDashboard();
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
}

export function useDeleteInvestment(portfolioId: string) {
  const queryClient = useQueryClient();
  const invalidateDashboard = useInvalidateDashboard();

  return useMutation({
    mutationFn: (id: string) => investmentApi.deleteInvestment(portfolioId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INVESTMENTS_QUERY_KEY });
      queryClient.invalidateQueries({
        queryKey: [...INVESTMENTS_QUERY_KEY, { portfolioId }],
      });
      invalidateDashboard();
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
}
