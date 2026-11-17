import { describe, it, expect } from 'vitest';
import {
  calculateFdMaturity,
  calculateRdMaturity,
  calculateGoldPurityWeight,
} from '../utils/financialCalculators';

describe('Financial Calculators', () => {
  describe('calculateFdMaturity', () => {
    it('calculates quarterly compounding correctly for 1 year @ 7.1%', () => {
      // P = 100,000, r = 0.071, n = 4, t = 1
      // A = 100000 * (1 + 0.071/4)^4 = 100000 * (1.01775)^4 = 100000 * 1.072916 = ~107,291.60
      const result = calculateFdMaturity({
        principal: 100000,
        annualRatePct: 7.1,
        tenureValue: 1,
        tenureUnit: 'years',
        compoundingFrequency: 'quarterly',
        payoutType: 'cumulative',
      });

      expect(result.maturityAmount).toBeCloseTo(107291.6, 0);
      expect(result.totalInterestEarned).toBeCloseTo(7291.6, 0);
      expect(result.effectiveAnnualYieldPct).toBeCloseTo(7.29, 2);
      expect(result.tenureInYears).toBe(1);
    });

    it('handles simple interest correctly', () => {
      const result = calculateFdMaturity({
        principal: 50000,
        annualRatePct: 6,
        tenureValue: 2,
        tenureUnit: 'years',
        compoundingFrequency: 'simple',
      });

      expect(result.maturityAmount).toBe(56000);
      expect(result.totalInterestEarned).toBe(6000);
      expect(result.effectiveAnnualYieldPct).toBe(6);
    });

    it('returns zero interest for invalid zero inputs', () => {
      const result = calculateFdMaturity({
        principal: 0,
        annualRatePct: 7,
        tenureValue: 1,
        tenureUnit: 'years',
      });
      expect(result.totalInterestEarned).toBe(0);
      expect(result.maturityAmount).toBe(0);
    });
  });

  describe('calculateRdMaturity', () => {
    it('calculates 12-month recurring deposit maturity', () => {
      const result = calculateRdMaturity({
        monthlyInstallment: 5000,
        annualRatePct: 7.0,
        tenureMonths: 12,
      });

      expect(result.totalDeposited).toBe(60000);
      expect(result.maturityAmount).toBeGreaterThan(60000);
      expect(result.totalInterestEarned).toBeGreaterThan(2000);
    });
  });

  describe('calculateGoldPurityWeight', () => {
    it('calculates pure 24K gold weight from 22K', () => {
      // 10g of 22K gold = 10 * (22/24) = 9.167g
      const pureWeight = calculateGoldPurityWeight(10, '22K');
      expect(pureWeight).toBeCloseTo(9.167, 3);
    });

    it('keeps 24K gold at 100% pure weight', () => {
      const pureWeight = calculateGoldPurityWeight(10, '24K');
      expect(pureWeight).toBe(10);
    });

    it('converts 18K gold correctly', () => {
      // 10g of 18K = 10 * 0.75 = 7.5g
      const pureWeight = calculateGoldPurityWeight(10, '18K');
      expect(pureWeight).toBe(7.5);
    });
  });
});
