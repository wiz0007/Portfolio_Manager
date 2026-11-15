export type AssetCategory =
  | 'cash'
  | 'fixed_income'
  | 'equity'
  | 'mutual_funds'
  | 'gold'
  | 'real_estate'
  | 'crypto';

export type InvestmentType =
  | 'savings_account'
  | 'current_account'
  | 'cash_balance'
  | 'fixed_deposit'
  | 'recurring_deposit'
  | 'bond'
  | 'stock'
  | 'listed_stock'
  | 'mutual_fund'
  | 'physical_gold'
  | 'digital_gold'
  | 'gold_etf'
  | 'sovereign_gold_bond'
  | 'real_estate'
  | 'residential_property'
  | 'commercial_property'
  | 'land_plot'
  | 'cryptocurrency';

export type AssetType = InvestmentType;

export interface AssetTypeConfig {
  id: InvestmentType;
  name: string;
  description: string;
  hasContractualMaturity: boolean;
  supportsFutureProjection: boolean;
  requiresMarketData: boolean;
  defaultValuationMethod: string;
}

export interface AssetCategoryConfig {
  id: AssetCategory;
  name: string;
  description: string;
  iconName: string;
  colorClass: string;
  types: AssetTypeConfig[];
}

export type ValuationMethod =
  | 'MANUAL'
  | 'MARKET_PRICE'
  | 'MARKET_FEED'
  | 'NAV'
  | 'NAV_FEED'
  | 'CONTRACTUAL_CALCULATION'
  | 'GOVERNMENT_REFERENCE'
  | 'APPRAISAL'
  | 'USER_ESTIMATE'
  | 'BANK_BALANCE';

export type TransactionType =
  | 'BUY'
  | 'SELL'
  | 'DEPOSIT'
  | 'WITHDRAWAL'
  | 'DIVIDEND'
  | 'INTEREST'
  | 'TRANSFER';
