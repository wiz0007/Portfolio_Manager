import { PriceFreshnessStatus } from '@/features/watchlists/types';

export interface DashboardUser {
  id: string;
  full_name: string;
  email: string;
}

export interface DashboardRecentPortfolio {
  id: string;
  name: string;
  base_currency: string;
  created_at: string;
  updated_at?: string;
}

export interface SelectedPortfolio {
  id: string;
  name: string;
  base_currency: string;
}

export interface CurrencySummary {
  currency: string;
  total_current_value: string;
  total_invested_capital: string;
  absolute_gain_loss: string;
  gain_loss_percentage: string | null;
  valued_investment_count: number;
  unvalued_investment_count: number;
  total_investment_count: number;
}

export interface DataCompleteness {
  total_active_holdings: number;
  valued_holdings: number;
  unvalued_holdings: number;
  stale_holdings: number;
  missing_price_holdings: number;
  awaiting_verification_holdings?: number;
  unsupported_holdings?: number;
  completeness_percentage: number;
}

export interface DashboardOverview {
  user: DashboardUser;
  portfolio_count: number;
  recent_portfolios: DashboardRecentPortfolio[];
  selected_portfolio?: SelectedPortfolio | null;
  is_combined?: boolean;
  active_investment_count?: number;
  summary?: CurrencySummary | null;
  totals_by_currency?: Record<string, CurrencySummary>;
  data_completeness?: DataCompleteness;
  calculated_at?: string;
}

export interface AssetClassAllocation {
  category: string;
  display_name: string;
  total_value: string;
  percentage: string;
  count: number;
}

export interface PortfolioAllocation {
  portfolio_id: string;
  portfolio_name: string;
  total_value: string;
  percentage: string;
  count: number;
}

export interface TopHoldingAllocation {
  id: string;
  display_name: string;
  category: string;
  total_value: string;
  percentage: string;
}

export interface AssetAllocationResponse {
  currency: string;
  denominator_value: string;
  valued_count: number;
  unvalued_count: number;
  has_unvalued_assets: boolean;
  asset_class_allocation: AssetClassAllocation[];
  portfolio_allocation: PortfolioAllocation[];
  top_holdings_allocation: TopHoldingAllocation[];
  allocations_by_currency?: Record<string, any>;
}

export interface HoldingOverviewItem {
  id: string;
  display_name: string;
  category: string;
  asset_type: string;
  portfolio_id: string;
  portfolio_name: string;
  is_active: boolean;
  currency: string;
  quantity?: string | null;
  invested_capital: string;
  current_value: string;
  absolute_gain_loss: string;
  gain_loss_percentage: string | null;
  valuation_date: string;
  valuation_source: string;
  valuation_status?: string;
  price_freshness: PriceFreshnessStatus;
  is_stale: boolean;
  price_effective_at: string | null;
  price_published_at: string | null;
  price_age_seconds: number | null;
}

export interface HoldingsOverviewResponse {
  count: number;
  limit: number;
  offset: number;
  results: HoldingOverviewItem[];
}

export interface RecentActivityItem {
  id: string;
  investment_id: string;
  investment_name: string;
  portfolio_id: string;
  portfolio_name: string;
  transaction_type: string;
  transaction_date: string;
  units: string;
  price_per_unit: string;
  amount: string;
  gross_amount?: string | null;
  fees: string;
  taxes: string;
  net_cash_flow?: string | null;
  currency: string;
  notes?: string;
  created_at: string;
}

export interface DataQualityCategoryItem {
  id: string;
  display_name: string;
  category: string;
  asset_type: string;
  currency: string;
  current_value: string;
  reason?: string;
}

export interface DataQualityCategory {
  count: number;
  label: string;
  description: string;
  items: DataQualityCategoryItem[];
}

export interface DataQualityResponse {
  overall_status: 'HEALTHY' | 'WARNING' | 'INCOMPLETE';
  total_active_holdings: number;
  categories: {
    valued: DataQualityCategory;
    stale: DataQualityCategory;
    missing_price: DataQualityCategory;
    awaiting_verification: DataQualityCategory;
    unsupported: DataQualityCategory;
  };
}
