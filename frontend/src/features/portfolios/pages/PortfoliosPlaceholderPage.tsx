import React from 'react';
import { Briefcase, ArrowRight, Layers, ShieldCheck } from 'lucide-react';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Link } from 'react-router-dom';

export const PortfoliosPlaceholderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Portfolios</h1>
        <p className="text-sm text-slate-400">Manage multi-asset portfolios across stocks, crypto, mutual funds, and real estate.</p>
      </div>

      <Card className="border-indigo-500/30 bg-gradient-to-br from-slate-900 to-indigo-950/40 p-8 text-center text-slate-100">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 mb-4">
          <Briefcase className="h-7 w-7" />
        </div>
        <CardTitle className="text-xl font-semibold text-white mb-2">
          Portfolio Management — Coming in Sprint 3
        </CardTitle>
        <CardDescription className="mx-auto max-w-lg text-sm text-slate-300 mb-6">
          Full multi-asset portfolio creation, asset allocation models, and transaction logging will be delivered in the upcoming Sprint 3 milestone. No fake financial metrics are displayed.
        </CardDescription>

        <div className="mx-auto grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-3 text-left mb-6">
          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Layers className="h-4 w-4" /> Multi-Asset
            </div>
            <p className="text-xs text-slate-400">Group stocks, crypto, funds, and real estate in a single unified view.</p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <ShieldCheck className="h-4 w-4" /> Neon Isolation
            </div>
            <p className="text-xs text-slate-400">Strict per-user ownership and relational consistency via PostgreSQL.</p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Briefcase className="h-4 w-4" /> Asset Tracking
            </div>
            <p className="text-xs text-slate-400">Buy, sell, dividend, and deposit transaction history with audit logging.</p>
          </div>
        </div>

        <Link to="/dashboard">
          <Button variant="outline" className="text-white border-slate-700 hover:bg-slate-800">
            Return to Dashboard <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </Card>
    </div>
  );
};
