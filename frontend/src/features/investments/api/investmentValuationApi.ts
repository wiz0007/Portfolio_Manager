import { apiClient } from '@/services/api/client';
import { InvestmentValuationItem } from '../types/investmentApiTypes';
import {
  PerformanceMetrics,
  ProjectionRequestPayload,
  ProjectionResponse,
} from '../types/valuationTypes';

export interface RecordManualValuationPayload {
  amount: number | string;
  valuation_date?: string;
  notes?: string;
  valuation_method?: string;
}

export const investmentValuationApi = {
  /**
   * Recalculates investment holding's valuation based on deterministic asset strategy.
   * Persists an immutable snapshot and updates Investment.current_value.
   */
  async calculateValuation(investmentId: string): Promise<InvestmentValuationItem> {
    return apiClient.post<InvestmentValuationItem>(
      `/investments/${investmentId}/valuations/calculate/`
    );
  },

  /**
   * Retrieves chronological list of valuation snapshots.
   */
  async getValuations(investmentId: string): Promise<InvestmentValuationItem[]> {
    return apiClient.get<InvestmentValuationItem[]>(
      `/investments/${investmentId}/valuations/`
    );
  },

  /**
   * Records a manual point-in-time valuation snapshot.
   */
  async recordManualValuation(
    investmentId: string,
    payload: RecordManualValuationPayload
  ): Promise<InvestmentValuationItem> {
    return apiClient.post<InvestmentValuationItem>(
      `/investments/${investmentId}/valuations/`,
      payload
    );
  },

  /**
   * Fetches holding performance metrics: cost basis, current value, absolute & percentage return.
   */
  async getPerformance(investmentId: string): Promise<PerformanceMetrics> {
    return apiClient.get<PerformanceMetrics>(
      `/investments/${investmentId}/performance/`
    );
  },

  /**
   * Computes deterministic future value projections across multiple scenarios.
   * Strictly non-mutating.
   */
  async calculateProjection(
    investmentId: string,
    payload: ProjectionRequestPayload = {}
  ): Promise<ProjectionResponse> {
    return apiClient.post<ProjectionResponse>(
      `/investments/${investmentId}/projections/calculate/`,
      payload
    );
  },
};
