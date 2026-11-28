export interface HoldingPoint {
  date: string;
  quantity: string;
  cost_basis: string;
  market_price: string | null;
  market_value: string | null;
  unrealized_pnl: string | null;
  realized_pnl: string;
  total_pnl: string | null;
  is_price_available: boolean;
}

export interface InvestmentTimelineEntry {
  id: string;
  date: string;
  type: string;
  units: string;
  price_per_unit: string;
  gross_amount: string;
  fees: string;
  taxes: string;
  net_cash_flow: string;
  notes?: string;
}

export interface InvestmentPerformance {
  investment_id: string;
  currency: string;
  current_quantity: string;
  initial_invested_capital: string;
  net_invested_capital: string;
  current_cost_basis: string;
  current_market_price: string | null;
  current_market_value: string | null;
  realized_pnl: string;
  unrealized_pnl: string | null;
  total_pnl: string | null;
  absolute_return_pct: string | null;
  cagr_pct: string | null;
  xirr_pct: string | null;
  xirr_status: string;
  first_transaction_date: string | null;
  latest_transaction_date: string | null;
  timeline: InvestmentTimelineEntry[];
  history: HoldingPoint[];
  data_completeness: {
    total_days: number;
    days_with_price: number;
    has_transactions: boolean;
    reconciliation_status?: string;
    reconciliation_notes?: string[];
  };
}

export interface PortfolioTimeSeriesPoint {
  date: string;
  market_value: string;
  invested_capital: string;
  realized_pnl: string;
  unrealized_pnl: string;
  total_pnl: string;
  net_cash_flow_on_date: string;
}

export interface HoldingPerformanceSummary {
  investment_id: string;
  current_quantity: string;
  cost_basis: string;
  market_value: string;
  realized_pnl: string;
  unrealized_pnl: string;
  total_pnl: string;
  absolute_return_pct: string | null;
  xirr_pct: string | null;
  is_active: boolean;
}

export interface PortfolioPerformance {
  portfolio_id: string;
  portfolio_name: string;
  currency: string;
  current_value: string;
  total_invested_capital: string;
  current_cost_basis: string;
  realized_pnl: string;
  unrealized_pnl: string;
  total_pnl: string;
  absolute_return_pct: string | null;
  cagr_pct: string | null;
  xirr_pct: string | null;
  xirr_status: string;
  active_holdings_count: number;
  closed_holdings_count: number;
  history: PortfolioTimeSeriesPoint[];
  holdings_summary: HoldingPerformanceSummary[];
  data_completeness: {
    total_holdings: number;
    active_holdings: number;
    has_cash_flows: boolean;
  };
}

export interface AllocationItem {
  key: string;
  name: string;
  market_value: string;
  percentage: string;
  holding_count: number;
}

export interface PortfolioAllocation {
  portfolio_id: string | null;
  currency: string;
  total_market_value: string;
  by_asset_category: AllocationItem[];
  by_instrument: AllocationItem[];
}

export interface Benchmark {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
}

export interface NormalizedPoint {
  date: string;
  target_value: string;
  benchmark_value: string;
  target_raw: string;
  benchmark_raw: string;
}

export interface BenchmarkComparison {
  target_id: string;
  target_type: string;
  benchmark_id: string;
  benchmark_symbol: string;
  benchmark_name: string;
  start_date: string;
  end_date: string;
  target_total_return_pct: string;
  benchmark_total_return_pct: string;
  excess_return_pct: string;
  points: NormalizedPoint[];
}
