import React from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  BarChart3,
  User,
  ShieldCheck,
  Database,
  ArrowRight,
  Plus,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { useCurrentUser } from '@/features/authentication/hooks/useAuth';
import { useDashboardOverview } from '@/features/dashboard/hooks/useDashboard';
import { useHealthCheck } from '@/shared/hooks/useHealth';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';

export const DashboardPage: React.FC = () => {
  const { data: currentUser } = useCurrentUser();
  const { data: overview, isLoading } = useDashboardOverview();
  const { data: healthData } = useHealthCheck();

  const user = overview?.user || currentUser;
  const portfolioCount = overview?.portfolio_count ?? 0;
  const recentPortfolios = overview?.recent_portfolios ?? [];

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const isDbConnected = healthData?.database === 'connected';

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-800 bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 p-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Active Session
            </span>
            <span className="text-xs text-slate-400">
              | DB Status: {isDbConnected ? 'Connected' : 'Verifying'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Welcome back, {user?.full_name || 'Investor'}!
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Your investment intelligence dashboard is ready. Manage your assets and financial health in one place.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link to="/settings/profile">
            <Button variant="outline" size="sm" className="text-slate-300 border-slate-700 hover:text-white">
              <User className="mr-1.5 h-3.5 w-3.5" /> Edit Profile
            </Button>
          </Link>
          <Link to="/portfolios/new">
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
              <Plus className="mr-1.5 h-3.5 w-3.5" /> New Portfolio
            </Button>
          </Link>
        </div>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Portfolios Created
            </span>
            <Briefcase className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {isLoading ? <span className="text-slate-600">...</span> : portfolioCount}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {portfolioCount === 0 ? 'No active portfolios yet' : `${portfolioCount} active portfolio${portfolioCount > 1 ? 's' : ''}`}
          </p>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Database Connectivity
            </span>
            <Database className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-lg font-bold text-emerald-400">
            {isDbConnected ? 'PostgreSQL Connected' : 'Checking connection...'}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Verified backend health probe
          </p>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Security Protocol
            </span>
            <ShieldCheck className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-2 text-lg font-bold text-cyan-300">
            Session Cookies
          </div>
          <p className="mt-1 text-xs text-slate-500">
            HTTP-only • CSRF Enforced
          </p>
        </Card>
      </div>

      {/* Main Content Grid: Portfolios & Analytics Preview */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Portfolio Section */}
        <Card className="border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <CardTitle className="text-lg font-semibold text-white">Your Portfolios</CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Real user portfolio containers
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-400">
                  Total: {portfolioCount}
                </span>
                <Link to="/portfolios">
                  <Button variant="ghost" size="sm" className="text-xs text-indigo-400 hover:text-indigo-300 p-1">
                    View All &rarr;
                  </Button>
                </Link>
              </div>
            </div>

            {/* If zero portfolios: Empty state */}
            {portfolioCount === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/50 p-8 text-center my-4">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800/80 text-slate-400 mb-3">
                  <Briefcase className="h-6 w-6" />
                </div>
                <h3 className="text-sm font-semibold text-white mb-1">
                  You haven't created a portfolio yet
                </h3>
                <p className="mx-auto max-w-sm text-xs text-slate-400 mb-4">
                  Create your first portfolio to start organizing your investment containers and currency allocations.
                </p>
                <Link to="/portfolios/new">
                  <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
                    <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Portfolio
                  </Button>
                </Link>
              </div>
            ) : (
              /* Recent Portfolios List */
              <div className="space-y-3 my-4">
                {recentPortfolios.map((portfolio) => (
                  <Link
                    key={portfolio.id}
                    to={`/portfolios/${portfolio.id}`}
                    className="flex items-center justify-between p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors group"
                  >
                    <div className="min-w-0 pr-3">
                      <div className="text-sm font-medium text-white group-hover:text-indigo-400 transition-colors truncate">
                        {portfolio.name}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5">
                        <Calendar className="h-3 w-3" />
                        <span>Created {formatDate(portfolio.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {portfolio.base_currency}
                      </span>
                      <ArrowRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="pt-2 text-[11px] text-slate-500 border-t border-slate-800/80 flex items-center justify-between">
            <span>Actual PostgreSQL portfolio records</span>
            <Link to="/portfolios/new" className="text-indigo-400 hover:text-indigo-300 font-medium">
              + New Portfolio
            </Link>
          </div>
        </Card>

        {/* Analytics Section (Sprint 4 Preview) */}
        <Card className="border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <CardTitle className="text-lg font-semibold text-white">Performance Analytics</CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  CAGR, XIRR, risk engine and AI insights
                </CardDescription>
              </div>
              <span className="rounded bg-purple-950/60 border border-purple-500/30 px-2 py-0.5 text-[11px] font-medium text-purple-300 flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> Sprint 4
              </span>
            </div>

            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/50 p-8 text-center my-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-purple-900/20 text-purple-400 border border-purple-500/30 mb-3">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">
                Financial Analytics & Intelligence
              </h3>
              <p className="mx-auto max-w-sm text-xs text-slate-400 mb-4">
                Detailed CAGR calculations, benchmark comparisons, and OpenAI LLM financial recommendations are scheduled for Sprint 4.
              </p>
              <Link to="/analytics">
                <Button size="sm" variant="outline" className="text-purple-300 border-purple-800/50 hover:bg-purple-950/40">
                  Explore Analytics Roadmap <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>

          <div className="pt-2 text-[11px] text-slate-500 border-t border-slate-800/80 flex items-center justify-between">
            <span>Sprint 4 Foundation</span>
            <span className="text-purple-400 font-medium">Upcoming Sprint</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
