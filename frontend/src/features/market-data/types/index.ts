export type AssetClassType =
  | 'EQUITY'
  | 'MUTUAL_FUND'
  | 'COMMODITY'
  | 'FIXED_INCOME'
  | 'REAL_ESTATE'
  | 'CRYPTO'
  | 'INDEX'
  | 'CASH_EQUIVALENT';

export interface InstrumentReferenceData {
  sector: string;
  industry: string;
  market_cap_category: string;
  lot_size: number;
  tick_size: string;
  website: string;
  details?: Record<string, unknown>;
}

export interface MarketQuote {
  id?: string;
  instrument_id?: string;
  symbol: string;
  price: string;
  open_price?: string | null;
  high_price?: string | null;
  low_price?: string | null;
  close_price?: string | null;
  volume?: number | null;
  change_amount?: string | null;
  change_percent?: string | null;
  provider: string;
  is_synthetic: boolean;
  interval?: string;
  currency: string;
  timestamp: string;
}

export interface Instrument {
  id: string;
  symbol: string;
  name: string;
  asset_class: AssetClassType;
  exchange: string;
  currency: string;
  isin?: string | null;
  is_active: boolean;
  reference_data?: InstrumentReferenceData | null;
  latest_quote?: MarketQuote | null;
  created_at: string;
  updated_at: string;
}

export interface HistoricalPoint {
  timestamp: string;
  price: string;
  open_price?: string | null;
  high_price?: string | null;
  low_price?: string | null;
  close_price?: string | null;
  volume?: number | null;
  change_amount?: string | null;
  change_percent?: string | null;
  interval: string;
  is_synthetic: boolean;
}

export interface MarketOverviewItem {
  id: string;
  symbol: string;
  name: string;
  asset_class: string;
  exchange: string;
  price: string;
  change_amount: string;
  change_percent: string;
  is_synthetic: boolean;
  timestamp: string;
}

export interface MarketOverviewData {
  indices: MarketOverviewItem[];
  equities: MarketOverviewItem[];
  mutual_funds: MarketOverviewItem[];
  is_demo_mode: boolean;
  demo_notice: string;
}

export interface ProviderHealthReport {
  name: string;
  is_available: boolean;
  latency_ms?: number | null;
  last_checked: string;
  message: string;
  mode: string;
  metadata?: Record<string, unknown>;
}
