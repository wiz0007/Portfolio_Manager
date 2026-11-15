import { apiClient } from '@/services/api/client';
import {
  CreateInvestmentPayload,
  InvestmentDetailItem,
  InvestmentListItem,
  UpdateInvestmentPayload,
} from '../types/investmentApiTypes';

export const investmentApi = {
  async getInvestments(portfolioId?: string, category?: string): Promise<InvestmentListItem[]> {
    const params = new URLSearchParams();
    if (portfolioId) params.append('portfolio_id', portfolioId);
    if (category) params.append('category', category);

    const query = params.toString() ? `?${params.toString()}` : '';
    const url = portfolioId
      ? `/portfolios/${portfolioId}/investments/${query}`
      : `/investments/${query}`;

    return apiClient.get<InvestmentListItem[]>(url);
  },

  async getInvestment(portfolioId: string, id: string): Promise<InvestmentDetailItem> {
    return apiClient.get<InvestmentDetailItem>(`/portfolios/${portfolioId}/investments/${id}/`);
  },

  async createInvestment(payload: CreateInvestmentPayload): Promise<InvestmentDetailItem> {
    const url = `/portfolios/${payload.portfolio}/investments/`;
    return apiClient.post<InvestmentDetailItem>(url, payload);
  },

  async updateInvestment(
    portfolioId: string,
    id: string,
    payload: UpdateInvestmentPayload
  ): Promise<InvestmentDetailItem> {
    return apiClient.patch<InvestmentDetailItem>(
      `/portfolios/${portfolioId}/investments/${id}/`,
      payload
    );
  },

  async deleteInvestment(portfolioId: string, id: string): Promise<void> {
    return apiClient.delete<void>(`/portfolios/${portfolioId}/investments/${id}/`);
  },
};
