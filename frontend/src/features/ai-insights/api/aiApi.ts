import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';
import {
  AIExplainPayload,
  AIExplainResponse,
  AIStatusResponse,
} from '../types';

export const aiKeys = {
  all: ['ai-insights'] as const,
  status: () => [...aiKeys.all, 'status'] as const,
};

export const useAiStatus = () => {
  return useQuery<AIStatusResponse>({
    queryKey: aiKeys.status(),
    queryFn: async () => {
      return apiClient.get<AIStatusResponse>('/ai/status/');
    },
    staleTime: 5 * 60 * 1000,
  });
};

export const useAiExplain = () => {
  return useMutation<AIExplainResponse, Error, AIExplainPayload>({
    mutationFn: async (payload: AIExplainPayload) => {
      return apiClient.post<AIExplainResponse>('/ai/explain/', payload);
    },
  });
};
