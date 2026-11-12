import React from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Briefcase,
  Edit2,
  Calendar,
  Layers,
  Clock,
  Loader2,
  ShieldAlert,
} from 'lucide-react';
import { usePortfolio } from '../hooks/usePortfolios';
import { Card, CardTitle } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';

export const PortfolioDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: portfolio, isLoading, isError } = usePortfolio(id || '');

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-theme-text-muted">
        <Loader2 className="h-8 w-8 animate-spin text-theme-primary mb-2" />
        <p className="text-sm">Loading portfolio details...</p>
      </div>
    );
  }

  if (isError || !portfolio) {
    return (
      <div className="max-w-md mx-auto text-center py-20 space-y-4">
        <div className="h-12 w-12 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-semibold text-theme-text">Portfolio Unavailable</h2>
        <p className="text-xs text-theme-text-muted">
          This portfolio does not exist or you do not have permission to access it.
        </p>
        <Link to="/portfolios">
          <Button variant="outline" className="border-theme-border text-theme-text">
            Back to Portfolios
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Navigation & Header */}
      <div className="space-y-3">
        <div>
          <Link
            to="/portfolios"
            className="inline-flex items-center text-xs font-medium text-theme-text-muted hover:text-theme-text transition-colors"
          >
            <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Portfolios
          </Link>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-theme-primary-subtle text-theme-primary border border-theme-primary/30">
              <Briefcase className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold tracking-tight text-theme-text">{portfolio.name}</h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-theme-primary-subtle text-theme-primary border border-theme-primary/20 font-mono">
                  {portfolio.base_currency}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-theme-text-muted mt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" /> Created {formatDate(portfolio.created_at)}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" /> Updated {formatDate(portfolio.updated_at)}
                </span>
              </div>
            </div>
          </div>

          <Button
            onClick={() => navigate(`/portfolios/${portfolio.id}/edit`)}
            variant="outline"
            className="text-theme-text border-theme-border hover:bg-theme-hover shrink-0"
          >
            <Edit2 className="mr-2 h-4 w-4" /> Edit Portfolio
          </Button>
        </div>
      </div>

      {/* Description Card */}
      <Card className="border-theme-border bg-theme-card p-6 shadow-sm">
        <CardTitle className="text-sm font-semibold uppercase tracking-wider text-theme-text-muted mb-2">
          Portfolio Overview & Strategy
        </CardTitle>
        <p className="text-sm text-theme-text-secondary leading-relaxed">
          {portfolio.description || (
            <span className="text-theme-text-muted italic">No description provided for this portfolio.</span>
          )}
        </p>
      </Card>

      {/* Holdings & Instruments Section */}
      <Card className="border-theme-border bg-theme-card/60 border-dashed p-10 text-center space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-theme-surface text-theme-text-muted border border-theme-border">
          <Layers className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-theme-text">Holdings & Assets</h3>
        <p className="mx-auto max-w-lg text-xs text-theme-text-muted leading-relaxed">
          Asset tracking, instrument management, transaction ledger, and real-time market valuations are scheduled for Sprint 5.
        </p>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-theme-surface border border-theme-border text-[11px] text-theme-text-secondary font-mono">
          Container ID: {portfolio.id}
        </div>
      </Card>
    </div>
  );
};
