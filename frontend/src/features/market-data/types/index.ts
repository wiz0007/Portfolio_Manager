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

export type InstrumentRequestStatus =
  | 'PENDING'
  | 'MATCHED'
  | 'APPROVED'
  | 'MORE_INFO_REQUESTED'
  | 'REJECTED'
  | 'DUPLICATE';

export interface InstrumentRequest {
  id: string;
  user_email: string;
  raw_name: string;
  asset_class: AssetClassType;
  product_type?: string;
  symbol: string;
  exchange: string;
  isin?: string | null;
  scheme_code?: string | null;
  notes: string;
  status: InstrumentRequestStatus;
  matched_instrument?: string | null;
  matched_instrument_symbol?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface InstrumentCoverage {
  id: string;
  instrument: string;
  symbol: string;
  canonical_name: string;
  asset_class: string;
  price_type: string;
  currency: string;
  unit: string;
  cadence: string;
  market_timezone: string;
  freshness_hours: number;
  grace_period_hours: number;
  preferred_source: string;
  status: string;
  last_attempt_at?: string | null;
  last_published_at?: string | null;
  notes?: string;
}

export type ObservationStatus = 'DRAFT' | 'PENDING_REVIEW' | 'PUBLISHED' | 'REJECTED';

export interface PriceObservation {
  id: string;
  instrument: string;
  symbol: string;
  instrument_name: string;
  price_type: string;
  value: string;
  currency: string;
  unit: string;
  effective_at: string;
  source: string;
  source_reference?: string;
  notes?: string;
  status: ObservationStatus;
  is_synthetic: boolean;
  recorded_by: string;
  recorded_by_email?: string;
  published_by?: string | null;
  published_by_email?: string | null;
  published_at?: string | null;
  rejection_reason?: string;
  correction_of?: string | null;
  correction_reason?: string;
  created_at: string;
}

export interface MarketDataWorklistItem {
  id: string;
  worklist: string;
  instrument: string;
  coverage?: string | null;
  canonical_name: string;
  symbol: string;
  exchange: string;
  isin?: string | null;
  asset_class: string;
  product_type: string;
  expected_price_type: string;
  currency: string;
  unit: string;
  effective_date: string;
  due_reason: string;
  status: string;
  last_published_price?: string | null;
  last_published_date?: string | null;
  source_guidance: string;
  notes: string;
}

export interface MarketDataWorklist {
  id: string;
  worklist_date: string;
  status: string;
  total_items: number;
  completed_items: number;
  metadata?: Record<string, unknown>;
  items: MarketDataWorklistItem[];
  generated_at: string;
}

export interface ImportRowError {
  row_number: number;
  field: string;
  error: string;
  raw_data?: Record<string, unknown>;
}

export interface ImportPreviewResult {
  filename: string;
  total_rows: number;
  valid_count: number;
  error_count: number;
  valid_rows: Array<{
    row_number: number;
    instrument_id: string;
    symbol: string;
    instrument_name: string;
    price_type: string;
    value: string;
    currency: string;
    unit: string;
    effective_at: string;
    source: string;
    source_reference?: string;
    notes?: string;
  }>;
  errors: ImportRowError[];
}
