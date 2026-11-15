/**
 * Precision financial calculation utilities for Investment Preview
 * All calculations are client-side previews and adhere to strict rounding conventions.
 */

export interface FdCalculationParams {
  principal: number;
  annualRatePct: number;
  tenureValue: number;
  tenureUnit: 'days' | 'months' | 'years';
  compoundingFrequency?: 'quarterly' | 'monthly' | 'half_yearly' | 'annually' | 'simple';
  payoutType?: 'cumulative' | 'monthly_payout' | 'quarterly_payout';
}

export interface FdCalculationResult {
  maturityAmount: number;
  totalInterestEarned: number;
  effectiveAnnualYieldPct: number;
  tenureInYears: number;
}

export const calculateFdMaturity = (params: FdCalculationParams): FdCalculationResult => {
  const { principal, annualRatePct, tenureValue, tenureUnit, compoundingFrequency = 'quarterly', payoutType = 'cumulative' } = params;

  if (principal <= 0 || annualRatePct <= 0 || tenureValue <= 0) {
    return {
      maturityAmount: principal,
      totalInterestEarned: 0,
      effectiveAnnualYieldPct: 0,
      tenureInYears: 0,
    };
  }

  // Convert tenure to years
  let tenureYears = 0;
  if (tenureUnit === 'years') tenureYears = tenureValue;
  else if (tenureUnit === 'months') tenureYears = tenureValue / 12;
  else if (tenureUnit === 'days') tenureYears = tenureValue / 365;

  const r = annualRatePct / 100;

  // Simple interest or non-cumulative periodic payout
  if (compoundingFrequency === 'simple' || payoutType === 'monthly_payout' || payoutType === 'quarterly_payout') {
    const totalInterest = principal * r * tenureYears;
    return {
      maturityAmount: Math.round((principal + totalInterest) * 100) / 100,
      totalInterestEarned: Math.round(totalInterest * 100) / 100,
      effectiveAnnualYieldPct: annualRatePct,
      tenureInYears: tenureYears,
    };
  }

  // Compounding frequency n
  let n = 4; // default Indian quarterly compounding
  if (compoundingFrequency === 'monthly') n = 12;
  else if (compoundingFrequency === 'half_yearly') n = 2;
  else if (compoundingFrequency === 'annually') n = 1;

  // A = P * (1 + r/n)^(n * t)
  const maturity = principal * Math.pow(1 + r / n, n * tenureYears);
  const totalInterest = maturity - principal;
  const yieldPct = tenureYears > 0 ? ((maturity - principal) / (principal * tenureYears)) * 100 : annualRatePct;

  return {
    maturityAmount: Math.round(maturity * 100) / 100,
    totalInterestEarned: Math.round(totalInterest * 100) / 100,
    effectiveAnnualYieldPct: Math.round(yieldPct * 100) / 100,
    tenureInYears: Math.round(tenureYears * 100) / 100,
  };
};

export interface RdCalculationParams {
  monthlyInstallment: number;
  annualRatePct: number;
  tenureMonths: number;
}

export interface RdCalculationResult {
  totalDeposited: number;
  maturityAmount: number;
  totalInterestEarned: number;
}

export const calculateRdMaturity = (params: RdCalculationParams): RdCalculationResult => {
  const { monthlyInstallment, annualRatePct, tenureMonths } = params;
  if (monthlyInstallment <= 0 || annualRatePct <= 0 || tenureMonths <= 0) {
    return { totalDeposited: 0, maturityAmount: 0, totalInterestEarned: 0 };
  }

  const totalDeposited = monthlyInstallment * tenureMonths;
  const r = annualRatePct / 100;

  // Standard Indian Bank quarterly compounding formula on recurring installments
  let maturity = 0;
  for (let m = 1; m <= tenureMonths; m++) {
    // each installment stays for (tenureMonths - m + 1) months
    const t = (tenureMonths - m + 1) / 12;
    maturity += monthlyInstallment * Math.pow(1 + r / 4, 4 * t);
  }

  const totalInterest = maturity - totalDeposited;

  return {
    totalDeposited: Math.round(totalDeposited * 100) / 100,
    maturityAmount: Math.round(maturity * 100) / 100,
    totalInterestEarned: Math.max(0, Math.round(totalInterest * 100) / 100),
  };
};

export const calculateGoldPurityWeight = (
  grossWeightGrams: number,
  purityKarat: number | string
): number => {
  if (grossWeightGrams <= 0) return 0;
  const karatNum = typeof purityKarat === 'number' ? purityKarat : parseInt(purityKarat.toString().replace(/K/i, ''), 10);
  if (isNaN(karatNum) || karatNum <= 0) return grossWeightGrams;
  const ratio = Math.min(1, karatNum / 24);
  return Math.round(grossWeightGrams * ratio * 1000) / 1000;
};
