import { apiClient } from '@/services/api/client';
import {
  CreatePortfolioPayload,
  Portfolio,
  UpdatePortfolioPayload,
} from '../types';

export const portfoliosApi = {
  async getPortfolios(): Promise<Portfolio[]> {
    return apiClient.get<Portfolio[]>('/portfolios/');
  },

  async getPortfolio(id: string): Promise<Portfolio> {
    return apiClient.get<Portfolio>(`/portfolios/${id}/`);
  },

  async createPortfolio(payload: CreatePortfolioPayload): Promise<Portfolio> {
    return apiClient.post<Portfolio>('/portfolios/', payload);
  },

  async updatePortfolio(id: string, payload: UpdatePortfolioPayload): Promise<Portfolio> {
    return apiClient.patch<Portfolio>(`/portfolios/${id}/`, payload);
  },

  async deletePortfolio(id: string): Promise<void> {
    return apiClient.delete<void>(`/portfolios/${id}/`);
  },
};
