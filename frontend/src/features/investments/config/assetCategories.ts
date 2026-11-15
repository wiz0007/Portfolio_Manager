import { AssetCategoryConfig, AssetTypeConfig } from '../types/investmentTypes';

export const ASSET_CATEGORIES: AssetCategoryConfig[] = [
  {
    id: 'cash',
    name: 'Cash & Banking',
    description: 'Savings accounts, current accounts, and liquid cash balances with interest tracking.',
    iconName: 'Landmark',
    colorClass: 'text-emerald-400 bg-emerald-500/10',
    types: [
      {
        id: 'savings_account',
        name: 'Savings Account',
        description: 'Interest-earning bank deposit with balance tracking and auto-sweep facilities.',
        hasContractualMaturity: false,
        supportsFutureProjection: true,
        requiresMarketData: false,
        defaultValuationMethod: 'BANK_BALANCE',
      },
      {
        id: 'current_account',
        name: 'Current Account',
        description: 'Transactional checking account with zero or operational interest rates.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: false,
        defaultValuationMethod: 'BANK_BALANCE',
      },
      {
        id: 'cash_balance',
        name: 'Physical Cash Balance',
        description: 'Physical cash held in domestic or foreign currencies.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: false,
        defaultValuationMethod: 'MANUAL',
      },
    ],
  },
  {
    id: 'fixed_income',
    name: 'Fixed Income & Deposits',
    description: 'Contractual term deposits, recurring deposits, and sovereign/corporate bonds.',
    iconName: 'ShieldCheck',
    colorClass: 'text-cyan-400 bg-cyan-500/10',
    types: [
      {
        id: 'fixed_deposit',
        name: 'Fixed Deposit (FD)',
        description: 'Term deposit with principal lock-in, compounding interest, and maturity values.',
        hasContractualMaturity: true,
        supportsFutureProjection: true,
        requiresMarketData: false,
        defaultValuationMethod: 'CONTRACTUAL_CALCULATION',
      },
      {
        id: 'recurring_deposit',
        name: 'Recurring Deposit (RD)',
        description: 'Periodic monthly installment deposit yielding compound maturity value.',
        hasContractualMaturity: true,
        supportsFutureProjection: true,
        requiresMarketData: false,
        defaultValuationMethod: 'CONTRACTUAL_CALCULATION',
      },
      {
        id: 'bond',
        name: 'Bonds & Debentures',
        description: 'Corporate NCDs, government securities, and coupon-bearing debt paper.',
        hasContractualMaturity: true,
        supportsFutureProjection: true,
        requiresMarketData: true,
        defaultValuationMethod: 'MARKET_PRICE',
      },
    ],
  },
  {
    id: 'equity',
    name: 'Equity & Stocks',
    description: 'Direct shares in companies listed on national or international exchanges.',
    iconName: 'TrendingUp',
    colorClass: 'text-blue-400 bg-blue-500/10',
    types: [
      {
        id: 'listed_stock',
        name: 'Listed Stocks / Shares',
        description: 'Company shares traded on stock exchanges (NSE, BSE, NASDAQ, etc.).',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: true,
        defaultValuationMethod: 'MARKET_PRICE',
      },
    ],
  },
  {
    id: 'mutual_funds',
    name: 'Mutual Funds',
    description: 'Professional pooled funds across equity, debt, and hybrid asset classes.',
    iconName: 'PieChart',
    colorClass: 'text-violet-400 bg-violet-500/10',
    types: [
      {
        id: 'mutual_fund',
        name: 'Mutual Fund Scheme',
        description: 'Units held in active or passive schemes with daily Net Asset Value (NAV).',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: true,
        defaultValuationMethod: 'NAV',
      },
    ],
  },
  {
    id: 'gold',
    name: 'Gold & Precious Metals',
    description: 'Sovereign gold bonds, physical bars/coins, gold ETFs, and digital gold holdings.',
    iconName: 'Coins',
    colorClass: 'text-amber-400 bg-amber-500/10',
    types: [
      {
        id: 'physical_gold',
        name: 'Physical Gold',
        description: 'Gold coins, bullion bars, and hallmarked jewellery with purity specifications.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: true,
        defaultValuationMethod: 'USER_ESTIMATE',
      },
      {
        id: 'digital_gold',
        name: 'Digital Gold',
        description: 'Fractional gold stored in insured vaults via fintech providers.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: true,
        defaultValuationMethod: 'MARKET_PRICE',
      },
      {
        id: 'gold_etf',
        name: 'Gold ETF',
        description: 'Exchange-traded units representing physical gold benchmarks.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: true,
        defaultValuationMethod: 'MARKET_PRICE',
      },
      {
        id: 'sovereign_gold_bond',
        name: 'Sovereign Gold Bond (SGB)',
        description: 'Government gold-backed securities with 2.5% annual coupon and 8-year maturity.',
        hasContractualMaturity: true,
        supportsFutureProjection: true,
        requiresMarketData: true,
        defaultValuationMethod: 'CONTRACTUAL_CALCULATION',
      },
    ],
  },
  {
    id: 'real_estate',
    name: 'Real Estate',
    description: 'Physical residential homes, commercial plots, and land properties.',
    iconName: 'Building2',
    colorClass: 'text-emerald-400 bg-emerald-500/10',
    types: [
      {
        id: 'residential_property',
        name: 'Residential Property',
        description: 'Apartments, villas, and independent houses with rental yield tracking.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: false,
        defaultValuationMethod: 'APPRAISAL',
      },
      {
        id: 'commercial_property',
        name: 'Commercial Property',
        description: 'Retail shops, offices, and warehouses with lease cash flows.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: false,
        defaultValuationMethod: 'APPRAISAL',
      },
      {
        id: 'land_plot',
        name: 'Plot / Agricultural Land',
        description: 'Undeveloped land plots with regional circle-rate benchmarking.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: false,
        defaultValuationMethod: 'GOVERNMENT_REFERENCE',
      },
    ],
  },
  {
    id: 'crypto',
    name: 'Cryptocurrency',
    description: 'Decentralized digital assets and network tokens.',
    iconName: 'Bitcoin',
    colorClass: 'text-orange-400 bg-orange-500/10',
    types: [
      {
        id: 'cryptocurrency',
        name: 'Cryptocurrency Token',
        description: 'Network-aware native or contract tokens held across exchanges or wallets.',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: true,
        defaultValuationMethod: 'MARKET_PRICE',
      },
    ],
  },
];

export const getCategoryConfig = (categoryId: string): AssetCategoryConfig | undefined => {
  return ASSET_CATEGORIES.find((cat) => cat.id === categoryId);
};

export const getAssetTypeConfig = (typeId: string): AssetTypeConfig | undefined => {
  for (const cat of ASSET_CATEGORIES) {
    const found = cat.types.find((t) => t.id === typeId);
    if (found) return found;
  }
  return undefined;
};
