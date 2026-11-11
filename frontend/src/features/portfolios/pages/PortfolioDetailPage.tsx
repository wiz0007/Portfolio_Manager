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
      <div className="py-24 flex flex-col items-center justify-center text-slate-400">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500 mb-2" />
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
        <h2 className="text-lg font-semibold text-white">Portfolio Unavailable</h2>
        <p className="text-xs text-slate-400">
          This portfolio does not exist or you do not have permission to access it.
        </p>
        <Link to="/portfolios">
          <Button variant="outline" className="border-slate-800 text-slate-300">
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
            className="inline-flex items-center text-xs font-medium text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Portfolios
          </Link>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
              <Briefcase className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold tracking-tight text-white">{portfolio.name}</h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                  {portfolio.base_currency}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
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
            className="bg-slate-800 hover:bg-slate-700 text-white shrink-0 border border-slate-700"
          >
            <Edit2 className="mr-2 h-4 w-4" /> Edit Portfolio
          </Button>
        </div>
      </div>

      {/* Description Card */}
      <Card className="border-slate-800 bg-slate-900/60 p-6">
        <CardTitle className="text-sm font-semibold text-white uppercase tracking-wider text-slate-400 mb-2">
          Portfolio Overview & Strategy
        </CardTitle>
        <p className="text-sm text-slate-300 leading-relaxed">
          {portfolio.description || (
            <span className="text-slate-500 italic">No description provided for this portfolio.</span>
          )}
        </p>
      </Card>

      {/* Holdings & Instruments Section */}
      <Card className="border-slate-800 bg-slate-900/40 border-dashed p-10 text-center space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-slate-400 border border-slate-700">
          <Layers className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-white">Holdings & Assets</h3>
        <p className="mx-auto max-w-lg text-xs text-slate-400 leading-relaxed">
          Asset tracking, instrument management, transaction ledger, and real-time market valuations are scheduled for Sprint 4.
        </p>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-[11px] text-slate-300 font-mono">
          Container ID: {portfolio.id}
        </div>
      </Card>
    </div>
  );
};
