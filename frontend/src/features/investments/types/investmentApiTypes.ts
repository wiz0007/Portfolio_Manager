export interface InvestmentListItem {
  id: string;
  portfolio: string;
  category: string;
  asset_type: string;
  display_name: string;
  currency: string;
  is_active: boolean;
  valuation_method: string;
  initial_value: string | number;
  current_value: string | number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface InvestmentTransactionItem {
  id: string;
  transaction_type: string;
  transaction_date: string;
  units: string | number;
  price_per_unit: string | number;
  amount: string | number;
  gross_amount?: string | number;
  fees: string | number;
  taxes?: string | number;
  net_cash_flow?: string | number;
  currency: string;
  notes?: string;
  created_at: string;
}

export interface InvestmentValuationItem {
  id: string;
  valuation_date: string;
  amount: string | number;
  currency?: string;
  valuation_method?: string;
  source: string;
  source_reference?: string;
  observed_at?: string;
  notes?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface InvestmentDetailItem extends InvestmentListItem {
  instrument?: string | null;
  details: Record<string, any> | null;
  transactions: InvestmentTransactionItem[];
  valuations: InvestmentValuationItem[];
}

export interface CreateInvestmentPayload {
  portfolio: string;
  instrument?: string;
  instrument_id?: string;
  category: string;
  asset_type: string;
  display_name?: string;
  currency?: string;
  notes?: string;
  valuation_method?: string;
  initial_value?: number;
  current_value?: number;
  details: Record<string, any>;
}

export interface UpdateInvestmentPayload {
  display_name?: string;
  is_active?: boolean;
  notes?: string;
  valuation_method?: string;
  current_value?: number;
  details?: Record<string, any>;
}
