import React from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  BarChart3,
  User,
  Database,
  ArrowRight,
  Plus,
  Calendar,
  Sparkles,
  AlertTriangle,
  RotateCw,
  ShieldCheck,
} from 'lucide-react';
import { useCurrentUser } from '@/features/authentication/hooks/useAuth';
import { useDashboardOverview } from '@/features/dashboard/hooks/useDashboard';
import { useHealthCheck } from '@/shared/hooks/useHealth';
import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import styles from './DashboardPage.module.css';

export const DashboardPage: React.FC = () => {
  const { data: currentUser } = useCurrentUser();
  const {
    data: overview,
    isLoading,
    isError,
    refetch,
  } = useDashboardOverview();
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
    <div className={styles.container}>
      {/* 1. Header with Hierarchy & Actions */}
      <header className={styles.headerRow}>
        <div>
          <div className={styles.headerMeta}>
            <span className={styles.statusBadge}>
              <span className={`${styles.dot} bg-emerald-400`} />
              Active Session
            </span>
            <span>| DB Status:</span>
            <span className={`inline-block ${styles.dot} ${dbHealth.dot}`} />
            <span className={dbHealth.color}>{dbHealth.label}</span>
          </div>
          <h1 className={styles.title}>
            Welcome back, {user?.full_name || 'Investor'}!
          </h1>
        </div>

        <div className={styles.headerActions}>
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
        </div>
      </header>

      {/* 2. Error State Banner */}
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

      {/* 3. Overview Stat Cards */}
      <section className={styles.metricsGrid} aria-label="Key Metrics">
        {/* Metric 1: Portfolios Count */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <span className={styles.metricLabel}>Portfolios Created</span>
            <Briefcase className="h-4 w-4 text-theme-primary" />
          </div>
          <div className={styles.metricValue}>
            {isLoading && !overview ? (
              <span className="text-theme-text-muted animate-pulse">...</span>
            ) : isError && !overview ? (
              <span className="text-theme-text-muted">—</span>
            ) : (
              overview?.portfolio_count ?? 0
            )}
          </div>
          <p className={styles.metricSubtext}>
            {isLoading && !overview
              ? 'Loading active portfolios...'
              : isError && !overview
              ? 'Unable to load count'
              : overview?.portfolio_count === 0
              ? 'No active portfolios yet'
              : `${overview?.portfolio_count} active portfolio${(overview?.portfolio_count ?? 0) > 1 ? 's' : ''}`}
          </p>
        </div>

        {/* Metric 2: Database Connectivity */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <span className={styles.metricLabel}>Database Connectivity</span>
            <Database className={`h-4 w-4 ${dbHealth.color}`} />
          </div>
          <div className={`${styles.metricValue} ${dbHealth.color}`} style={{ fontSize: '1.125rem' }}>
            {dbHealth.label}
          </div>
          <p className={styles.metricSubtext}>
            Verified backend health probe
          </p>
        </div>

        {/* Metric 3: Security & Session Protection */}
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <span className={styles.metricLabel}>Session Security</span>
            <ShieldCheck className="h-4 w-4 text-theme-primary" />
          </div>
          <div className={styles.metricValue} style={{ fontSize: '1.125rem' }}>
            Active Session
          </div>
          <p className={styles.metricSubtext}>
            HTTP-only cookies & CSRF verification
          </p>
        </div>
      </section>

      {/* 4. Main Content Grid: Portfolios & Analytics Preview */}
      <div className={styles.sectionsGrid}>
        {/* Portfolio Section */}
        <div className={styles.sectionCard}>
          <div>
            <div className={styles.sectionHeader}>
              <div>
                <h2 className={styles.sectionTitle}>Your Portfolios</h2>
                <span className="text-xs text-theme-text-muted">Real user portfolio containers</span>
              </div>
              <div className="flex items-center gap-2">
                {overview && (
                  <span className={styles.sectionCount}>
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
                    className="p-3.5 rounded-lg bg-theme-surface border border-theme-border animate-pulse h-16"
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
              <div className="rounded-xl border border-dashed border-theme-border bg-theme-surface p-8 text-center my-4">
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
              <div className={styles.portfolioList}>
                {overview.recent_portfolios.map((portfolio) => (
                  <Link
                    key={portfolio.id}
                    to={`/portfolios/${portfolio.id}`}
                    className={styles.portfolioRow}
                  >
                    <div className="min-w-0 pr-3">
                      <div className={styles.portfolioName}>
                        {portfolio.name}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-theme-text-muted mt-0.5">
                        <Calendar className="h-3 w-3" />
                        <span>Created {formatDate(portfolio.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={styles.currencyBadge}>
                        {portfolio.base_currency}
                      </span>
                      <ArrowRight className="h-3.5 w-3.5 text-theme-text-muted" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className={styles.sectionFooter}>
            <span>Actual PostgreSQL portfolio records</span>
            <Link to="/portfolios/new" className="text-theme-primary hover:underline font-medium">
              + New Portfolio
            </Link>
          </div>
        </div>

        {/* Analytics Section (Sprint 5 Roadmap) */}
        <div className={styles.sectionCard}>
          <div>
            <div className={styles.sectionHeader}>
              <div>
                <h2 className={styles.sectionTitle}>Performance Analytics</h2>
                <span className="text-xs text-theme-text-muted">CAGR, XIRR, risk engine and AI insights</span>
              </div>
              <span className="rounded bg-theme-accent-subtle border border-theme-accent/30 px-2 py-0.5 text-[11px] font-medium text-theme-accent flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> Upcoming
              </span>
            </div>

            <div className="rounded-xl border border-dashed border-theme-border bg-theme-surface p-8 text-center my-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-theme-accent-subtle text-theme-accent border border-theme-accent/30 mb-3">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-theme-text mb-1">
                Financial Analytics & Intelligence
              </h3>
              <p className="mx-auto max-w-sm text-xs text-theme-text-muted mb-4">
                Detailed CAGR calculations, benchmark comparisons, holdings performance, and AI-assisted financial recommendations are scheduled for the next release.
              </p>
              <Link to="/analytics">
                <Button size="sm" variant="outline" className="text-theme-text border-theme-border hover:bg-theme-hover">
                  Explore Analytics Roadmap <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>

          <div className={styles.sectionFooter}>
            <span>MVP Foundation Ready</span>
            <span className="text-theme-accent font-medium">Sprint 5 Scope</span>
          </div>
        </div>
      </div>
    </div>
  );
};
