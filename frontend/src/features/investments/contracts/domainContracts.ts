/**
 * Sprint 1 Domain Models & Backend API Contracts Specification
 * 
 * Defines the canonical backend data contracts for Sprint 2 persistent ledger,
 * aligning Django PostgreSQL models, DRF Serializers, and Frontend TypeScript interfaces.
 */

import { AssetCategory, AssetType, ValuationMethod, TransactionType } from '../types/investmentTypes';

export interface BaseEntityContract {
  id: string; // UUID v4
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

// 1. Core Investment Holding Container
export interface InvestmentContract extends BaseEntityContract {
  portfolio_id: string; // ForeignKey(Portfolio)
  user_id: number; // ForeignKey(User)
  category: AssetCategory;
  asset_type: AssetType;
  display_name: string;
  currency: string;
  is_active: boolean;
  notes?: string;
  valuation_method: ValuationMethod;
  last_valuation_amount?: number;
  last_valuation_date?: string;
}

// 2. Instrument Master (Market securities: Stocks, ETFs, Mutual Funds, SGBs)
export interface InstrumentContract extends BaseEntityContract {
  symbol: string;
  name: string;
  isin?: string;
  exchange?: 'NSE' | 'BSE' | 'NASDAQ' | 'NYSE' | 'LSE' | 'OTHER';
  asset_category: AssetCategory;
  asset_type: AssetType;
  currency: string;
  is_active: boolean;
}

// 3. Cash & Banking Domain Model
export interface CashAccountDetailContract extends BaseEntityContract {
  investment_id: string; // OneToOneField(Investment)
  bank_name: string;
  account_type: 'SAVINGS' | 'CURRENT' | 'SALARY' | 'SENIOR_CITIZEN' | 'NRE_NRO';
  masked_account_number?: string;
  interest_rate_pct?: number;
  interest_credit_frequency: 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'ANNUALLY';
  auto_sweep_enabled: boolean;
  sweep_out_threshold?: number;
  sweep_retained_balance?: number;
  sweep_increment?: number;
  overdraft_limit?: number;
}

// 4. Fixed Income & Term Deposit Domain Model
export interface DepositDetailContract extends BaseEntityContract {
  investment_id: string; // OneToOneField(Investment)
  institution_name: string;
  deposit_type: 'FIXED_DEPOSIT' | 'RECURRING_DEPOSIT';
  principal_amount: number;
  monthly_installment?: number;
  start_date: string; // YYYY-MM-DD
  maturity_date?: string; // YYYY-MM-DD
  tenure_value: number;
  tenure_unit: 'days' | 'months' | 'years';
  annual_rate_pct: number;
  compounding_frequency: 'quarterly' | 'monthly' | 'half_yearly' | 'annually' | 'simple';
  payout_type: 'cumulative' | 'monthly_payout' | 'quarterly_payout';
  is_senior_citizen: boolean;
  is_tax_saver: boolean;
  auto_renewal: boolean;
  maturity_amount_projected?: number;
}

// 5. Bond & Debenture Model
export interface BondDetailContract extends BaseEntityContract {
  investment_id: string;
  issuer_name: string;
  bond_name: string;
  isin?: string;
  face_value: number;
  quantity: number;
  purchase_price_per_unit: number;
  purchase_date: string;
  coupon_rate_pct: number;
  coupon_frequency: 'ANNUALLY' | 'SEMI_ANNUALLY' | 'QUARTERLY' | 'MONTHLY' | 'CUMULATIVE';
  maturity_date: string;
  credit_rating?: string;
}

// 6. Listed Equity Model
export interface EquityDetailContract extends BaseEntityContract {
  investment_id: string;
  instrument_id?: string; // Optional ForeignKey(Instrument)
  company_name: string;
  symbol: string;
  exchange: string;
  isin?: string;
  quantity: number;
  average_buy_price: number;
  brokerage_fees: number;
  statutory_taxes: number;
}

// 7. Mutual Fund Model
export interface MutualFundDetailContract extends BaseEntityContract {
  investment_id: string;
  amc_name: string;
  scheme_name: string;
  scheme_category: string;
  plan: 'DIRECT' | 'REGULAR';
  option: 'GROWTH' | 'IDCW_PAYOUT' | 'IDCW_REINVESTMENT';
  units: number;
  average_purchase_nav: number;
  is_sip: boolean;
  sip_amount?: number;
  sip_frequency?: string;
}

// 8. Gold & Bullion Model
export interface GoldDetailContract extends BaseEntityContract {
  investment_id: string;
  gold_variant: 'PHYSICAL' | 'DIGITAL' | 'ETF' | 'SGB';
  purity?: '24K' | '22K' | '18K' | '14K';
  physical_form?: 'COIN' | 'BAR' | 'JEWELLERY' | 'OTHER';
  gross_weight_grams?: number;
  pure_gold_weight_grams?: number;
  provider?: string; // MMTC-PAMP, SafeGold, RBI
  storage_location?: string;
  coupon_rate_pct?: number; // SGB 2.5%
  maturity_date?: string; // SGB 8-year
}

// 9. Real Estate Model
export interface RealEstateDetailContract extends BaseEntityContract {
  investment_id: string;
  property_name: string;
  property_type: 'RESIDENTIAL' | 'COMMERCIAL' | 'LAND' | 'INDUSTRIAL';
  property_use: 'SELF_OCCUPIED' | 'RENTED' | 'VACANT' | 'UNDER_CONSTRUCTION';
  state: string;
  city: string;
  locality: string;
  address_line?: string;
  plot_area?: number;
  built_up_area?: number;
  area_unit: 'SQ_FT' | 'SQ_METER' | 'BIGHA' | 'ACRE';
  ownership_percentage: number;
  purchase_price: number;
  purchase_date: string;
  stamp_duty_paid: number;
  registration_fee_paid: number;
  renovation_expenses: number;
  monthly_rental_income: number;
  valuation_method: ValuationMethod;
  estimated_current_value: number;
}

// 10. Crypto Model
export interface CryptoDetailContract extends BaseEntityContract {
  investment_id: string;
  token_name: string;
  symbol: string;
  network: string;
  contract_address?: string;
  quantity: number;
  purchase_price_per_token: number;
  wallet_type: 'HARDWARE_WALLET' | 'SOFTWARE_WALLET' | 'EXCHANGE' | 'OTHER';
  exchange_name?: string;
  transaction_hash?: string;
}

// 11. Transaction Ledger Model
export interface TransactionContract extends BaseEntityContract {
  investment_id: string;
  transaction_type: TransactionType;
  transaction_date: string; // ISO 8601
  quantity?: number;
  unit_price?: number;
  gross_amount: number;
  fees: number;
  taxes: number;
  net_amount: number;
  reference_number?: string;
  notes?: string;
}

// 12. Valuation Record
export interface ValuationContract extends BaseEntityContract {
  investment_id: string;
  valuation_date: string;
  valuation_amount: number;
  valuation_method: ValuationMethod;
  source_notes?: string;
}
