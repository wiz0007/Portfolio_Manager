export type PriceFreshnessStatus =
  | 'AVAILABLE'
  | 'STALE'
  | 'MISSING'
  | 'SYNTHETIC'
  | 'UNSUPPORTED'
  | 'AWAITING_VERIFICATION'
  | 'CONFLICTED';

export type MovementStatus =
  | 'CALCULATED'
  | 'UNAVAILABLE'
  | 'ZERO_BASE'
  | 'INCOMPATIBLE';

export interface WatchlistInstrument {
  id: string;
  symbol: string;
  name: string;
  asset_class: string;
  product_type: string;
  exchange: string;
  currency: string;
  isin: string | null;
  scheme_code: string | null;
  sector: string;
  industry: string;
  status: string;
}

export interface PriceMovement {
  change_amount: string | null;
  change_percent: string | null;
  previous_price: string | null;
  previous_effective_at: string | null;
  status: MovementStatus;
  notes: string;
}

export interface WatchlistMarketData {
  price: string | null;
  price_type?: string;
  currency: string;
  unit: string;
  effective_at: string | null;
  published_at?: string | null;
  age_seconds?: number | null;
  status: PriceFreshnessStatus;
  source: string;
  source_reference: string;
  is_synthetic: boolean;
  notes: string;
  movement: PriceMovement;
}

export interface WatchlistItem {
  id: string;
  instrument: WatchlistInstrument;
  notes: string;
  target_price: string | null;
  created_at: string;
  updated_at: string;
  market_data: WatchlistMarketData;
}

export interface AddWatchlistPayload {
  instrument_id: string;
  notes?: string;
  target_price?: string | number | null;
}

export interface HistoryPoint {
  timestamp: string;
  date: string;
  price: string;
  currency: string;
  unit: string;
  source: string;
  is_synthetic: boolean;
  open_price?: string | null;
  high_price?: string | null;
  low_price?: string | null;
  volume?: number | null;
}

export interface ChartDataPoint {
  date: string;
  close: string;
  open?: string | null;
  high?: string | null;
  low?: string | null;
  volume?: number | null;
}

export interface InstrumentHistoryResponse {
  instrument_id: string;
  symbol: string;
  series_id?: string;
  frequency?: string;
  price_type?: string;
  data_version?: number;
  last_effective_date?: string | null;
  last_published_at?: string | null;
  supported: boolean;
  period: string;
  start_date: string | null;
  end_date: string | null;
  currency: string;
  unit: string;
  trust_class?: string;
  message: string;
  points: HistoryPoint[];
  data?: ChartDataPoint[];
}

export interface InstrumentMarketStatus {
  instrument_id: string;
  symbol: string;
  coverage_configured: boolean;
  price_type: string;
  quotation_unit: string;
  freshness_hours: number | null;
  resolution_status: PriceFreshnessStatus;
  last_effective_at: string | null;
  source: string;
  is_synthetic: boolean;
  notes: string;
}
