import { describe, it, expect, vi, beforeEach } from 'vitest';
import { investmentApi } from '../api/investmentApi';
import { apiClient } from '@/services/api/client';
import { portfoliosApi } from '@/features/portfolios/api/portfoliosApi';

vi.mock('@/services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Investment and Portfolio API Lifecycle Contracts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('investmentApi Lifecycle', () => {
    it('constructs correct URL and query parameters for getInvestments', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);

      await investmentApi.getInvestments('port-123', 'equity');
      expect(apiClient.get).toHaveBeenCalledWith(
        '/portfolios/port-123/investments/?portfolio_id=port-123&category=equity'
      );
    });

    it('constructs correct URL for getInvestment detail', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ id: 'inv-456' });

      await investmentApi.getInvestment('port-123', 'inv-456');
      expect(apiClient.get).toHaveBeenCalledWith('/portfolios/port-123/investments/inv-456/');
    });

    it('posts full investment payload to portfolio endpoint on createInvestment', async () => {
      const payload = {
        portfolio: 'port-123',
        category: 'real_estate',
        asset_type: 'land_plot',
        display_name: 'Dehradun Orchard',
        currency: 'INR',
        details: {
          state: 'Uttarakhand',
          district: 'Dehradun',
          land_area: 2.5,
          area_unit: 'ACRE',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ id: 'inv-created', ...payload });

      const res = await investmentApi.createInvestment(payload as any);
      expect(apiClient.post).toHaveBeenCalledWith('/portfolios/port-123/investments/', payload);
      expect(res.id).toBe('inv-created');
    });

    it('sends patch payload to holding endpoint on updateInvestment', async () => {
      const updatePayload = {
        display_name: 'Updated Holding Name',
        current_value: 75000,
        notes: 'Updated notes',
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ id: 'inv-456', ...updatePayload });

      await investmentApi.updateInvestment('port-123', 'inv-456', updatePayload);
      expect(apiClient.patch).toHaveBeenCalledWith(
        '/portfolios/port-123/investments/inv-456/',
        updatePayload
      );
    });

    it('invokes delete on holding endpoint on deleteInvestment', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce(undefined);

      await investmentApi.deleteInvestment('port-123', 'inv-456');
      expect(apiClient.delete).toHaveBeenCalledWith('/portfolios/port-123/investments/inv-456/');
    });
  });

  describe('portfoliosApi Lifecycle', () => {
    it('constructs correct portfolio list and detail endpoints', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);
      await portfoliosApi.getPortfolios();
      expect(apiClient.get).toHaveBeenCalledWith('/portfolios/');

      vi.mocked(apiClient.get).mockResolvedValueOnce({ id: 'port-123' });
      await portfoliosApi.getPortfolio('port-123');
      expect(apiClient.get).toHaveBeenCalledWith('/portfolios/port-123/');
    });

    it('handles portfolio creation and patch payloads', async () => {
      const createData = { name: 'Tech Port', base_currency: 'USD' };
      vi.mocked(apiClient.post).mockResolvedValueOnce({ id: 'port-1', ...createData });
      await portfoliosApi.createPortfolio(createData as any);
      expect(apiClient.post).toHaveBeenCalledWith('/portfolios/', createData);

      const updateData = { name: 'Updated Tech Port' };
      vi.mocked(apiClient.patch).mockResolvedValueOnce({ id: 'port-1', ...updateData });
      await portfoliosApi.updatePortfolio('port-1', updateData);
      expect(apiClient.patch).toHaveBeenCalledWith('/portfolios/port-1/', updateData);
    });
  });
});
