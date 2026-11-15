import { describe, it, expect } from 'vitest';
import {
  savingsAccountSchema,
  fixedDepositSchema,
  recurringDepositSchema,
  stockSchema,
  physicalGoldSchema,
  realEstateSchema,
  cryptocurrencySchema,
} from '../schemas/investmentSchemas';

const validUuid = '123e4567-e89b-12d3-a456-426614174000';

describe('Investment Schemas Validation', () => {
  describe('savingsAccountSchema', () => {
    it('validates a valid savings account', () => {
      const result = savingsAccountSchema.safeParse({
        portfolio_id: validUuid,
        bank_name: 'HDFC Bank',
        account_nickname: 'Primary Salary',
        account_type: 'SAVINGS',
        current_balance: 50000,
        balance_date: '2026-11-15',
        interest_rate_pct: 3.0,
      });

      expect(result.success).toBe(true);
    });

    it('fails when sweep_out_threshold is less than retained_balance', () => {
      const result = savingsAccountSchema.safeParse({
        portfolio_id: validUuid,
        bank_name: 'SBI',
        account_nickname: 'Sweep Account',
        account_type: 'SAVINGS',
        current_balance: 50000,
        balance_date: '2026-11-15',
        auto_sweep_enabled: true,
        sweep_out_threshold: 20000,
        sweep_retained_balance: 25000, // Invalid: threshold < retained
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toContain(
          'Sweep-out threshold must be greater than or equal to retained balance'
        );
      }
    });
  });

  describe('fixedDepositSchema', () => {
    it('validates a valid fixed deposit', () => {
      const result = fixedDepositSchema.safeParse({
        portfolio_id: validUuid,
        bank_name: 'State Bank of India',
        deposit_nickname: 'SBI Amrit Kalash',
        principal_amount: 100000,
        start_date: '2026-01-01',
        tenure_value: 400,
        tenure_unit: 'days',
        maturity_date: '2027-02-05',
        annual_rate_pct: 7.1,
      });

      expect(result.success).toBe(true);
    });

    it('rejects when maturity_date is before start_date', () => {
      const result = fixedDepositSchema.safeParse({
        portfolio_id: validUuid,
        bank_name: 'State Bank of India',
        deposit_nickname: 'Invalid FD',
        principal_amount: 100000,
        start_date: '2026-06-01',
        tenure_value: 1,
        tenure_unit: 'years',
        maturity_date: '2026-01-01', // Before start
        annual_rate_pct: 7.1,
      });

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Maturity date must be after');
      }
    });
  });

  describe('stockSchema', () => {
    it('validates and auto-uppercases symbol', () => {
      const result = stockSchema.safeParse({
        portfolio_id: validUuid,
        company_name: 'Infosys Limited',
        symbol: 'infy',
        exchange: 'NSE',
        quantity: 25,
        purchase_price_per_share: 1500,
        purchase_date: '2026-11-01',
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.symbol).toBe('INFY');
      }
    });

    it('rejects negative quantity or price', () => {
      const result = stockSchema.safeParse({
        portfolio_id: validUuid,
        company_name: 'TCS',
        symbol: 'TCS',
        quantity: -10,
        purchase_price_per_share: 3500,
        purchase_date: '2026-11-01',
      });

      expect(result.success).toBe(false);
    });
  });

  describe('recurringDepositSchema', () => {
    it('validates a valid recurring deposit', () => {
      const result = recurringDepositSchema.safeParse({
        portfolio_id: validUuid,
        bank_name: 'SBI',
        deposit_nickname: 'Goal RD',
        monthly_installment: 5000,
        start_date: '2026-01-01',
        tenure_months: 12,
        annual_rate_pct: 6.8,
      });

      expect(result.success).toBe(true);
    });
  });

  describe('physicalGoldSchema', () => {
    it('validates physical gold holdings', () => {
      const result = physicalGoldSchema.safeParse({
        portfolio_id: validUuid,
        item_name: 'MMTC Gold Bar',
        gold_form: 'BAR',
        purity: '24K',
        gross_weight_grams: 10,
        purchase_price_total: 75000,
        purchase_date: '2026-10-01',
      });

      expect(result.success).toBe(true);
    });
  });

  describe('realEstateSchema', () => {
    it('validates real estate property entry', () => {
      const result = realEstateSchema.safeParse({
        portfolio_id: validUuid,
        property_name: 'Dehradun Residence',
        property_type: 'RESIDENTIAL',
        property_use: 'SELF_OCCUPIED',
        state: 'Uttarakhand',
        city: 'Dehradun',
        locality: 'Rajpur Road',
        ownership_percentage: 100,
        purchase_price: 6500000,
        purchase_date: '2025-05-10',
        estimated_current_value: 7200000,
      });

      expect(result.success).toBe(true);
    });
  });

  describe('cryptocurrencySchema', () => {
    it('accepts valid fractional crypto holding', () => {
      const result = cryptocurrencySchema.safeParse({
        portfolio_id: validUuid,
        token_name: 'Bitcoin',
        symbol: 'btc',
        network: 'Bitcoin',
        quantity: 0.054321,
        purchase_price_per_token: 5400000,
        purchase_date: '2026-10-15',
      });

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.symbol).toBe('BTC');
        expect(result.data.quantity).toBe(0.054321);
      }
    });
  });
});
