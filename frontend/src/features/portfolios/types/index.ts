export type SupportedCurrency =
  | 'INR'
  | 'USD'
  | 'EUR'
  | 'GBP'
  | 'JPY'
  | 'AUD'
  | 'CAD'
  | 'SGD'
  | 'CHF'
  | 'AED';

export const SUPPORTED_CURRENCIES: { code: SupportedCurrency; name: string; symbol: string }[] = [
  { code: 'INR', name: 'Indian Rupee', symbol: '₹' },
  { code: 'USD', name: 'US Dollar', symbol: '$' },
  { code: 'EUR', name: 'Euro', symbol: '€' },
  { code: 'GBP', name: 'British Pound', symbol: '£' },
  { code: 'JPY', name: 'Japanese Yen', symbol: '¥' },
  { code: 'AUD', name: 'Australian Dollar', symbol: 'A$' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$' },
  { code: 'SGD', name: 'Singapore Dollar', symbol: 'S$' },
  { code: 'CHF', name: 'Swiss Franc', symbol: 'CHF' },
  { code: 'AED', name: 'UAE Dirham', symbol: 'AED' },
];

export interface Portfolio {
  id: string;
  name: string;
  description: string;
  base_currency: SupportedCurrency;
  created_at: string;
  updated_at: string;
}

export interface CreatePortfolioPayload {
  name: string;
  description?: string;
  base_currency: SupportedCurrency;
}

export interface UpdatePortfolioPayload {
  name?: string;
  description?: string;
  base_currency?: SupportedCurrency;
}
