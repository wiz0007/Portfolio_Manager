import { z } from 'zod';

// Common currency enum
export const currencyEnum = z.enum(
  ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'SGD', 'CHF', 'AED'] as const,
  { errorMap: () => ({ message: 'Please select a supported currency.' }) }
);

// 1. Savings Account Form Schema
export const savingsAccountSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  bank_name: z.string().min(1, 'Bank name is required.').trim(),
  account_nickname: z.string().min(1, 'Account nickname is required.').max(100).trim(),
  account_type: z.enum(['SAVINGS', 'CURRENT', 'SALARY', 'SENIOR_CITIZEN', 'NRE_NRO']),
  currency: currencyEnum.default('INR'),
  masked_account_number: z.string().max(20).optional(),
  current_balance: z.number({ invalid_type_error: 'Balance must be a valid number.' }).min(0, 'Balance cannot be negative.'),
  balance_date: z.string().min(1, 'Balance effective date is required.'),
  interest_rate_pct: z.number().min(0, 'Interest rate cannot be negative.').max(30, 'Interest rate cannot exceed 30%.').optional(),
  interest_credit_frequency: z.enum(['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'ANNUALLY']).default('QUARTERLY'),
  auto_sweep_enabled: z.boolean().default(false),
  sweep_out_threshold: z.number().min(0).optional(),
  sweep_retained_balance: z.number().min(0).optional(),
  sweep_increment: z.number().min(0).optional(),
  notes: z.string().max(1000).optional(),
}).refine(
  (data) => {
    if (data.auto_sweep_enabled && data.sweep_out_threshold && data.sweep_retained_balance) {
      return data.sweep_out_threshold >= data.sweep_retained_balance;
    }
    return true;
  },
  {
    message: 'Sweep-out threshold must be greater than or equal to retained balance.',
    path: ['sweep_out_threshold'],
  }
);

// 2. Current Account Form Schema
export const currentAccountSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  bank_name: z.string().min(1, 'Bank name is required.').trim(),
  account_nickname: z.string().min(1, 'Account nickname is required.').max(100).trim(),
  account_type: z.literal('CURRENT').default('CURRENT'),
  currency: currencyEnum.default('INR'),
  masked_account_number: z.string().max(20).optional(),
  current_balance: z.number().min(0, 'Balance cannot be negative.'),
  balance_date: z.string().min(1, 'Balance effective date is required.'),
  overdraft_limit: z.number().min(0).default(0).optional(),
  notes: z.string().max(1000).optional(),
});

// 3. Fixed Deposit Form Schema
export const fixedDepositSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  bank_name: z.string().min(1, 'Bank or Institution name is required.').trim(),
  deposit_nickname: z.string().min(1, 'Deposit nickname is required.').max(100).trim(),
  currency: currencyEnum.default('INR'),
  principal_amount: z.number().positive('Principal amount must be greater than zero.'),
  start_date: z.string().min(1, 'Deposit start date is required.'),
  tenure_value: z.number().positive('Tenure must be greater than zero.'),
  tenure_unit: z.enum(['days', 'months', 'years']),
  maturity_date: z.string().min(1, 'Maturity date is required.'),
  annual_rate_pct: z.number().positive('Interest rate must be positive.').max(30, 'Interest rate cannot exceed 30%.'),
  compounding_frequency: z.enum(['quarterly', 'monthly', 'half_yearly', 'annually', 'simple']).default('quarterly'),
  payout_type: z.enum(['cumulative', 'monthly_payout', 'quarterly_payout']).default('cumulative'),
  is_senior_citizen: z.boolean().default(false),
  is_tax_saver: z.boolean().default(false),
  auto_renewal: z.boolean().default(false),
  notes: z.string().max(1000).optional(),
}).refine(
  (data) => new Date(data.maturity_date) > new Date(data.start_date),
  {
    message: 'Maturity date must be after the deposit start date.',
    path: ['maturity_date'],
  }
);

// 4. Recurring Deposit Form Schema
export const recurringDepositSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  bank_name: z.string().min(1, 'Bank name is required.').trim(),
  deposit_nickname: z.string().min(1, 'Deposit nickname is required.').max(100).trim(),
  currency: currencyEnum.default('INR'),
  monthly_installment: z.number().positive('Monthly installment must be positive.'),
  start_date: z.string().min(1, 'Start date is required.'),
  tenure_months: z.number().int().min(6, 'Minimum RD tenure is 6 months.').max(120, 'Maximum RD tenure is 120 months.'),
  annual_rate_pct: z.number().positive('Interest rate must be positive.').max(30),
  installment_due_day: z.number().int().min(1).max(31).default(5),
  notes: z.string().max(1000).optional(),
});

// 5. Listed Stock Form Schema
export const stockSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  company_name: z.string().min(1, 'Company name is required.').trim(),
  symbol: z.string().min(1, 'Stock ticker symbol is required.').toUpperCase().trim(),
  exchange: z.enum(['NSE', 'BSE', 'NASDAQ', 'NYSE', 'LSE', 'OTHER']).default('NSE'),
  currency: currencyEnum.default('INR'),
  isin: z.string().max(12).optional(),
  quantity: z.number().positive('Quantity must be greater than zero.'),
  purchase_price_per_share: z.number().positive('Purchase price must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  brokerage_fees: z.number().min(0, 'Brokerage fees cannot be negative.').default(0).optional(),
  taxes: z.number().min(0, 'Taxes cannot be negative.').default(0).optional(),
  notes: z.string().max(1000).optional(),
});

// 6. Mutual Fund Form Schema
export const mutualFundSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  amc_name: z.string().min(1, 'AMC / Fund House is required.').trim(),
  scheme_name: z.string().min(1, 'Scheme name is required.').trim(),
  scheme_category: z.string().min(1, 'Category is required.').trim(),
  plan: z.enum(['DIRECT', 'REGULAR']).default('DIRECT'),
  option: z.enum(['GROWTH', 'IDCW_PAYOUT', 'IDCW_REINVESTMENT']).default('GROWTH'),
  currency: currencyEnum.default('INR'),
  units: z.number().positive('Units must be greater than zero.'),
  purchase_nav: z.number().positive('Purchase NAV must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  is_sip: z.boolean().default(false),
  sip_amount: z.number().positive().optional(),
  sip_frequency: z.enum(['MONTHLY', 'WEEKLY', 'QUARTERLY']).optional(),
  notes: z.string().max(1000).optional(),
});

// 7. Bond Form Schema
export const bondSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  issuer_name: z.string().min(1, 'Issuer name is required.').trim(),
  bond_name: z.string().min(1, 'Bond title is required.').trim(),
  isin: z.string().max(12).optional(),
  face_value: z.number().positive('Face value must be positive.'),
  quantity: z.number().int().positive('Quantity must be at least 1.'),
  purchase_price_per_unit: z.number().positive('Purchase price must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  coupon_rate_pct: z.number().min(0, 'Coupon rate cannot be negative.').max(30),
  coupon_frequency: z.enum(['ANNUALLY', 'SEMI_ANNUALLY', 'QUARTERLY', 'MONTHLY', 'CUMULATIVE']).default('ANNUALLY'),
  maturity_date: z.string().min(1, 'Maturity date is required.'),
  credit_rating: z.string().max(20).optional(),
  notes: z.string().max(1000).optional(),
}).refine(
  (data) => new Date(data.maturity_date) > new Date(data.purchase_date),
  { message: 'Maturity date must be after purchase date.', path: ['maturity_date'] }
);

// 8. Physical Gold Form Schema
export const physicalGoldSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  item_name: z.string().min(1, 'Item description is required.').trim(),
  gold_form: z.enum(['COIN', 'BAR', 'JEWELLERY', 'OTHER']),
  purity: z.enum(['24K', '22K', '18K', '14K']).default('24K'),
  gross_weight_grams: z.number().positive('Gross weight must be positive.'),
  making_charges: z.number().min(0).default(0).optional(),
  purchase_price_total: z.number().positive('Total purchase price must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  storage_location: z.string().max(100).optional(),
  notes: z.string().max(1000).optional(),
});

// 9. Digital Gold Form Schema
export const digitalGoldSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  provider: z.string().min(1, 'Provider name (e.g. MMTC-PAMP, SafeGold) is required.').trim(),
  weight_grams: z.number().positive('Weight in grams must be positive.'),
  purchase_amount: z.number().positive('Purchase amount must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  notes: z.string().max(1000).optional(),
});

// 10. Gold ETF Form Schema
export const goldEtfSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  fund_name: z.string().min(1, 'Fund name is required.').trim(),
  symbol: z.string().min(1, 'ETF Symbol is required.').toUpperCase().trim(),
  exchange: z.enum(['NSE', 'BSE']).default('NSE'),
  units: z.number().positive('Units must be positive.'),
  purchase_price: z.number().positive('Purchase price per unit must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  brokerage_fees: z.number().min(0).default(0).optional(),
  notes: z.string().max(1000).optional(),
});

// 11. Sovereign Gold Bond (SGB) Form Schema
export const sovereignGoldBondSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  series_name: z.string().min(1, 'SGB Series name is required.').trim(),
  units_grams: z.number().int().positive('Number of grams must be at least 1.'),
  issue_price_per_gram: z.number().positive('Price per gram must be positive.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  coupon_rate_pct: z.number().default(2.5),
  maturity_date: z.string().min(1, 'Maturity date is required.'),
  notes: z.string().max(1000).optional(),
});

// 12. Real Estate Form Schema
export const realEstateSchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  property_name: z.string().min(1, 'Property name or identifier is required.').trim(),
  property_type: z.enum(['RESIDENTIAL', 'COMMERCIAL', 'LAND', 'INDUSTRIAL']),
  property_use: z.enum(['SELF_OCCUPIED', 'RENTED', 'VACANT', 'UNDER_CONSTRUCTION']),
  state: z.string().min(1, 'State is required.').trim(),
  city: z.string().min(1, 'City/Town is required.').trim(),
  locality: z.string().min(1, 'Locality is required.').trim(),
  address_line: z.string().max(255).optional(),
  plot_area: z.number().positive('Plot / Land area must be positive.').optional(),
  built_up_area: z.number().positive('Built-up area must be positive.').optional(),
  area_unit: z.enum(['SQ_FT', 'SQ_METER', 'BIGHA', 'ACRE']).default('SQ_FT'),
  ownership_percentage: z.number().min(1, 'Ownership must be at least 1%.').max(100, 'Ownership cannot exceed 100%.').default(100),
  purchase_price: z.number().min(0, 'Purchase price cannot be negative.'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  stamp_duty_paid: z.number().min(0).default(0).optional(),
  registration_fee_paid: z.number().min(0).default(0).optional(),
  renovation_expenses: z.number().min(0).default(0).optional(),
  monthly_rental_income: z.number().min(0).default(0).optional(),
  valuation_method: z.enum(['MANUAL', 'GOVERNMENT_REFERENCE', 'APPRAISAL', 'USER_ESTIMATE']).default('USER_ESTIMATE'),
  estimated_current_value: z.number().positive('Estimated value must be positive.'),
  notes: z.string().max(1000).optional(),
});

// 13. Cryptocurrency Form Schema
export const cryptocurrencySchema = z.object({
  portfolio_id: z.string().uuid('Please select a valid portfolio.'),
  token_name: z.string().min(1, 'Token name is required.').trim(),
  symbol: z.string().min(1, 'Symbol is required.').toUpperCase().trim(),
  network: z.string().min(1, 'Network / Blockchain is required.').trim(),
  contract_address: z.string().max(100).optional(),
  quantity: z.number().positive('Quantity must be greater than zero.'),
  purchase_price_per_token: z.number().positive('Purchase price must be positive.'),
  currency: currencyEnum.default('INR'),
  purchase_date: z.string().min(1, 'Purchase date is required.'),
  wallet_type: z.enum(['HARDWARE_WALLET', 'SOFTWARE_WALLET', 'EXCHANGE', 'OTHER']).default('EXCHANGE'),
  exchange_name: z.string().max(100).optional(),
  transaction_hash: z.string().max(150).optional(),
  notes: z.string().max(1000).optional(),
});

// 14. Plot / Agricultural Land Form Schema (Sprint 2 Specification)
export const agriculturalLandSchema = z
  .object({
    portfolio_id: z.string().uuid('Please select a valid portfolio.'),
    property_name: z.string().max(150).optional(),
    property_type: z.enum(['LAND', 'AGRICULTURAL', 'PLOT']).default('LAND'),
    land_classification: z
      .enum(['AGRICULTURAL', 'RESIDENTIAL', 'COMMERCIAL', 'OTHER'])
      .default('AGRICULTURAL'),
    country: z.string().default('India'),
    state: z.string().min(1, 'State is required.').trim(),
    district: z.string().min(1, 'District is required.').trim(),
    tehsil: z.string().max(100).optional(),
    locality: z.string().max(100).optional(),
    village: z.string().max(100).optional(),
    survey_or_plot_number: z.string().max(100).optional(),
    land_area: z.number().positive('Land area must be greater than zero.'),
    area_unit: z.enum(['SQ_FT', 'SQ_METER', 'BIGHA', 'ACRE']).default('ACRE'),
    ownership_percentage: z
      .number()
      .min(0.01, 'Ownership percentage must be greater than zero.')
      .max(100, 'Ownership cannot exceed 100%.')
      .default(100),
    acquisition_date: z.string().min(1, 'Acquisition date is required.'),
    purchase_price: z.number().min(0, 'Purchase price cannot be negative.'),
    registration_charges: z.number().min(0, 'Registration charges cannot be negative.').default(0).optional(),
    stamp_duty: z.number().min(0, 'Stamp duty cannot be negative.').default(0).optional(),
    other_acquisition_costs: z.number().min(0, 'Other acquisition costs cannot be negative.').default(0).optional(),
    estimated_current_value: z.number().min(0, 'Estimated value cannot be negative.').optional(),
    valuation_date: z.string().optional(),
    valuation_source: z.string().max(100).optional(),
    expected_annual_appreciation: z.number().min(0).max(100).optional(),
    notes: z.string().max(1000).optional(),
  })
  .refine(
    (data) => {
      if (data.valuation_date) {
        const valDate = new Date(data.valuation_date);
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        return valDate <= today;
      }
      return true;
    },
    {
      message: 'Valuation date cannot be in the future.',
      path: ['valuation_date'],
    }
  )
  .refine(
    (data) => {
      if (data.estimated_current_value && data.estimated_current_value > 0) {
        return Boolean(data.valuation_date);
      }
      return true;
    },
    {
      message: 'Valuation date is required when an estimated current value is provided.',
      path: ['valuation_date'],
    }
  );

// Inferred TypeScript Form Data Types
export type SavingsAccountFormData = z.infer<typeof savingsAccountSchema>;
export type CurrentAccountFormData = z.infer<typeof currentAccountSchema>;
export type FixedDepositFormData = z.infer<typeof fixedDepositSchema>;
export type RecurringDepositFormData = z.infer<typeof recurringDepositSchema>;
export type BondFormData = z.infer<typeof bondSchema>;
export type StockFormData = z.infer<typeof stockSchema>;
export type MutualFundFormData = z.infer<typeof mutualFundSchema>;
export type PhysicalGoldFormData = z.infer<typeof physicalGoldSchema>;
export type DigitalGoldFormData = z.infer<typeof digitalGoldSchema>;
export type GoldEtfFormData = z.infer<typeof goldEtfSchema>;
export type SovereignGoldBondFormData = z.infer<typeof sovereignGoldBondSchema>;
export type RealEstateFormData = z.infer<typeof realEstateSchema>;
export type AgriculturalLandFormData = z.infer<typeof agriculturalLandSchema>;
export type CryptocurrencyFormData = z.infer<typeof cryptocurrencySchema>;
