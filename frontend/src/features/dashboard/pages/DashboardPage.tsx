import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  User,
  Database,
  ArrowRight,
  Plus,
  Calendar,
  AlertTriangle,
  RotateCw,
  ShieldCheck,
  PlusCircle,
} from 'lucide-react';
import { useCurrentUser } from '@/features/authentication/hooks/useAuth';
import { useDashboardOverview } from '@/features/dashboard/hooks/useDashboard';
import { useHealthCheck } from '@/shared/hooks/useHealth';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';

import { PortfolioSelector } from '../components/PortfolioSelector';
import { PortfolioOverview } from '../components/PortfolioOverview';
import { AssetAllocationChart } from '../components/AssetAllocationChart';
import { HoldingsOverview } from '../components/HoldingsOverview';
import { RecentActivity } from '../components/RecentActivity';
import { ValuationDataQuality } from '../components/ValuationDataQuality';
import { WatchlistPreview } from '../components/WatchlistPreview';

export const DashboardPage: React.FC = () => {
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | undefined>(undefined);

  const { data: currentUser } = useCurrentUser();
  const {
    data: overview,
    isLoading,
    isError,
    refetch,
  } = useDashboardOverview(selectedPortfolioId);
  const { data: healthData, isLoading: isHealthLoading, isError: isHealthError } = useHealthCheck();

  const user = overview?.user || currentUser;

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

  const getDbHealthStatus = () => {
    if (isHealthLoading) {
      return {
        label: 'Checking connection...',
        color: 'text-amber-400',
        dot: 'bg-amber-400',
      };
    }
    if (isHealthError || healthData?.database !== 'connected') {
      return {
        label: 'Connection unavailable',
        color: 'text-rose-400',
        dot: 'bg-rose-400',
      };
    }
    return {
      label: 'Service connected',
      color: 'text-emerald-400',
      dot: 'bg-emerald-400',
    };
  };

  const dbHealth = getDbHealthStatus();

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-theme-border bg-gradient-to-r from-theme-card via-theme-surface to-theme-card p-6 shadow-sm transition-colors duration-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Active Session
            </span>
            <span className="text-xs text-theme-text-muted flex items-center gap-1.5">
              <span>| DB Status:</span>
              <span className={`inline-block h-1.5 w-1.5 rounded-full ${dbHealth.dot}`} />
              <span className={dbHealth.color}>{dbHealth.label}</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-theme-text">
            Welcome back, {user?.full_name || 'Investor'}!
          </h1>
          <p className="mt-1 text-sm text-theme-text-muted">
            Your investment intelligence dashboard is ready. Manage your assets and financial health in one place.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link to="/settings/profile">
            <Button variant="outline" size="sm" className="text-theme-text border-theme-border hover:bg-theme-hover">
              <User className="mr-1.5 h-3.5 w-3.5" /> Edit Profile
            </Button>
          </Link>
          <Link to="/portfolios/new">
            <Button size="sm" className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm">
              <Plus className="mr-1.5 h-3.5 w-3.5" /> New Portfolio
            </Button>
          </Link>
          <Link to="/investments/new">
            <Button size="sm" variant="outline" className="text-theme-text border-theme-border hover:bg-theme-hover">
              <PlusCircle className="mr-1.5 h-3.5 w-3.5 text-theme-primary" /> Add Investment
            </Button>
          </Link>
        </div>
      </div>

      {/* Scope Selector */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <PortfolioSelector
          selectedPortfolioId={selectedPortfolioId}
          onSelectPortfolio={setSelectedPortfolioId}
        />
        {overview?.calculated_at && (
          <span className="text-[11px] text-theme-text-muted font-medium">
            Calculated: {new Date(overview.calculated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      {/* API Error State Banner */}
      {isError && (
        <Card className="border-rose-900/40 bg-rose-950/20 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-rose-300">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0" />
            <div>
              <div className="text-sm font-semibold text-rose-200">
                Unable to load dashboard overview
              </div>
              <div className="text-xs text-rose-400/90 mt-0.5">
                A network or server error occurred while retrieving your portfolio records.
              </div>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetch()}
            className="border-rose-800 text-rose-200 hover:bg-rose-900/30 shrink-0"
          >
            <RotateCw className="mr-1.5 h-3.5 w-3.5" /> Retry
          </Button>
        </Card>
      )}

      {/* Section A: Comprehensive Portfolio Overview Metrics */}
      <PortfolioOverview overview={overview} isLoading={isLoading && !overview} />

      {/* Legacy Baseline Stat Cards (retained for backward compatibility and system health display) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-theme-border bg-theme-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              Portfolios Created
            </span>
            <Briefcase className="h-4 w-4 text-theme-primary" />
          </div>
          <div className="mt-2 text-2xl font-bold text-theme-text">
            {isLoading && !overview ? (
              <span className="text-theme-text-muted animate-pulse">...</span>
            ) : isError && !overview ? (
              <span className="text-theme-text-muted">—</span>
            ) : (
              overview?.portfolio_count ?? 0
            )}
          </div>
          <p className="mt-1 text-xs text-theme-text-muted">
            {isLoading && !overview
              ? 'Loading active portfolios...'
              : isError && !overview
              ? 'Unable to load count'
              : overview?.portfolio_count === 0
              ? 'No active portfolios yet'
              : `${overview?.portfolio_count} active portfolio${(overview?.portfolio_count ?? 0) > 1 ? 's' : ''}`}
          </p>
        </Card>

        <Card className="border-theme-border bg-theme-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              Database Connectivity
            </span>
            <Database className={`h-4 w-4 ${dbHealth.color}`} />
          </div>
          <div className={`mt-2 text-lg font-bold ${dbHealth.color}`}>
            {dbHealth.label}
          </div>
          <p className="mt-1 text-xs text-theme-text-muted">
            Verified backend health probe
          </p>
        </Card>

        <Card className="border-theme-border bg-theme-card p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              Session Security
            </span>
            <ShieldCheck className="h-4 w-4 text-theme-primary" />
          </div>
          <div className="mt-2 text-lg font-bold text-theme-text">
            Active Session
          </div>
          <p className="mt-1 text-xs text-theme-text-muted">
            HTTP-only cookies & CSRF verification
          </p>
        </Card>
      </div>

      {/* Sections C & F: Asset Allocation and Data Quality Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AssetAllocationChart portfolioId={selectedPortfolioId} />
        <ValuationDataQuality portfolioId={selectedPortfolioId} />
      </div>

      {/* Section D: Holdings Overview */}
      <HoldingsOverview portfolioId={selectedPortfolioId} />

      {/* Sections E & G: Recent Activity and Watchlist Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentActivity portfolioId={selectedPortfolioId} />
        <WatchlistPreview />
      </div>

      {/* Portfolios Container List */}
      <Card className="border-theme-border bg-theme-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <CardTitle className="text-lg font-semibold text-theme-text">Your Portfolios</CardTitle>
            <CardDescription className="text-xs text-theme-text-muted">
              Real user portfolio containers
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {overview && (
              <span className="rounded bg-theme-surface px-2 py-1 text-[11px] font-medium text-theme-text-secondary border border-theme-border">
                Total: {overview.portfolio_count}
              </span>
            )}
            <Link to="/portfolios">
              <Button variant="ghost" size="sm" className="text-xs text-theme-primary hover:bg-theme-hover p-1">
                View All &rarr;
              </Button>
            </Link>
          </div>
        </div>

        {/* Loading State Skeleton */}
        {isLoading && !overview && (
          <div className="space-y-3 my-4">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="p-3.5 rounded-lg bg-theme-surface/60 border border-theme-border animate-pulse h-16"
              />
            ))}
          </div>
        )}

        {/* Error State when no cached overview exists */}
        {isError && !overview && (
          <div className="rounded-xl border border-rose-900/30 bg-rose-950/20 p-6 text-center my-4">
            <AlertTriangle className="h-6 w-6 text-rose-400 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-rose-200 mb-1">
              Failed to load portfolios
            </h3>
            <p className="text-xs text-rose-400/90 mb-3">
              Could not retrieve your portfolio data. Please check your connection and try again.
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetch()}
              className="border-rose-800 text-rose-200 hover:bg-rose-900/30"
            >
              <RotateCw className="mr-1.5 h-3.5 w-3.5" /> Retry
            </Button>
          </div>
        )}

        {/* Empty State: Only when successfully loaded with 0 portfolios */}
        {overview && overview.portfolio_count === 0 && (
          <div className="rounded-xl border border-dashed border-theme-border bg-theme-surface/50 p-8 text-center my-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-theme-surface text-theme-text-muted mb-3 border border-theme-border">
              <Briefcase className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-theme-text mb-1">
              You haven't created a portfolio yet
            </h3>
            <p className="mx-auto max-w-sm text-xs text-theme-text-muted mb-4">
              Create your first portfolio to start organizing your investment containers and currency allocations.
            </p>
            <Link to="/portfolios/new">
              <Button size="sm" className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm">
                <Plus className="mr-1.5 h-3.5 w-3.5" /> Create Portfolio
              </Button>
            </Link>
          </div>
        )}

        {/* Recent Portfolios List: Only when overview has portfolios */}
        {overview && overview.portfolio_count > 0 && (
          <div className="space-y-3 my-4">
            {overview.recent_portfolios.map((portfolio) => (
              <Link
                key={portfolio.id}
                to={`/portfolios/${portfolio.id}`}
                className="flex items-center justify-between p-3.5 rounded-lg bg-theme-surface border border-theme-border hover:border-theme-primary/50 transition-colors group"
              >
                <div className="min-w-0 pr-3">
                  <div className="text-sm font-medium text-theme-text group-hover:text-theme-primary transition-colors truncate">
                    {portfolio.name}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-theme-text-muted mt-0.5">
                    <Calendar className="h-3 w-3" />
                    <span>Created {formatDate(portfolio.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-theme-primary-subtle text-theme-primary border border-theme-primary/30">
                    {portfolio.base_currency}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 text-theme-text-muted group-hover:text-theme-primary transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}

        <div className="pt-2 text-[11px] text-theme-text-muted border-t border-theme-border flex items-center justify-between">
          <span>Actual PostgreSQL portfolio records</span>
          <Link to="/portfolios/new" className="text-theme-primary hover:underline font-medium">
            + New Portfolio
          </Link>
        </div>
      </Card>
    </div>
  );
};
