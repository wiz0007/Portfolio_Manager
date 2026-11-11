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

export interface DashboardOverview {
  user: DashboardUser;
  portfolio_count: number;
  base_currency: string;
  recent_portfolios: DashboardRecentPortfolio[];
}
