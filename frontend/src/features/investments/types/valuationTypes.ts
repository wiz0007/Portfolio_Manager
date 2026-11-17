export interface PerformanceMetrics {
  investment_id: string;
  display_name: string;
  category: string;
  asset_type: string;
  currency: string;
  invested_amount: string;
  current_value: string;
  absolute_gain_loss: string;
  percentage_gain_loss: string;
  is_gain: boolean;
  last_valuation_date: string | null;
  valuation_method: string;
  source: string;
}

export interface ProjectionScheduleItem {
  year: number;
  invested_capital: string;
  projected_future_value: string;
  estimated_growth: string;
}

export interface ScenarioResult {
  scenario_name: string;
  annual_rate_percent: string;
  projected_future_value: string;
  total_invested_capital: string;
  total_estimated_growth: string;
  schedule: ProjectionScheduleItem[];
}

export interface ProjectionResponse {
  formula_id?: string;
  assumption_disclosures?: string;
  investment_id: string;
  display_name: string;
  category: string;
  currency: string;
  starting_value?: string;
  initial_principal: string;
  monthly_contribution: string;
  contribution_amount?: string;
  time_horizon_years: number;
  horizon_years?: string;
  contribution_timing: string;
  contribution_frequency_per_year?: number;
  compounding_frequency_per_year: number;
  scenarios: Record<string, ScenarioResult>;
}

export interface ProjectionRequestPayload {
  time_horizon_years?: number;
  monthly_contribution?: number | string;
  contribution_timing?: 'END_OF_PERIOD' | 'BEGINNING_OF_PERIOD';
  compounding_frequency_per_year?: number;
  custom_annual_rate?: number | string | null;
  scenarios?: string[];
}
