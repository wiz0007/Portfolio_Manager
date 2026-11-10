import React from 'react';
import { Eye, ArrowRight, BellRing, TrendingUp, Sparkles } from 'lucide-react';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Link } from 'react-router-dom';

export const WatchlistPlaceholderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Watchlist & Alerts</h1>
        <p className="text-sm text-slate-400">Track target equities, cryptocurrencies, and configure price action alerts.</p>
      </div>

      <Card className="border-cyan-500/30 bg-gradient-to-br from-slate-900 to-cyan-950/40 p-8 text-center text-slate-100">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-600/20 border border-cyan-500/40 text-cyan-400 mb-4">
          <Eye className="h-7 w-7" />
        </div>
        <CardTitle className="text-xl font-semibold text-white mb-2">
          Asset Watchlists — Planned Feature
        </CardTitle>
        <CardDescription className="mx-auto max-w-lg text-sm text-slate-300 mb-6">
          Custom multi-asset tracking lists, live price updates, and threshold notification triggers are scheduled for upcoming iterations.
        </CardDescription>

        <div className="mx-auto grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-3 text-left mb-6">
          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <TrendingUp className="h-4 w-4" /> Live Quotes
            </div>
            <p className="text-xs text-slate-400">NSE, BSE, and Crypto market feeds with historical caching.</p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <BellRing className="h-4 w-4" /> Smart Alerts
            </div>
            <p className="text-xs text-slate-400">Custom percentage swings, target price triggers, and notifications.</p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Sparkles className="h-4 w-4" /> Valuation Watch
            </div>
            <p className="text-xs text-slate-400">Expense ratio tracking and historical PE/PB evaluation.</p>
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
