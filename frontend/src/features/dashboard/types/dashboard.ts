export interface DashboardUser {
  id: string;
  full_name: string;
  email: string;
}

export interface DashboardOverview {
  user: DashboardUser;
  portfolio_count: number;
  recent_portfolios: any[];
}
