import React from 'react';
import { BarChart3, ArrowRight, LineChart, Cpu, Sparkles } from 'lucide-react';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Link } from 'react-router-dom';

export const AnalyticsPlaceholderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-theme-text">Analytics & Intelligence</h1>
        <p className="text-sm text-theme-text-muted">Deep performance analytics, risk indicators, and AI financial intelligence.</p>
      </div>

      <Card className="border-theme-border bg-theme-card p-8 text-center text-theme-text shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-theme-primary-subtle border border-theme-primary/30 text-theme-primary mb-4">
          <BarChart3 className="h-7 w-7" />
        </div>
        <CardTitle className="text-xl font-semibold text-theme-text mb-2">
          Analytics & Insights — Coming in Future Sprints
        </CardTitle>
        <CardDescription className="mx-auto max-w-lg text-sm text-theme-text-muted mb-6">
          Real-time performance metrics (XIRR, CAGR, Sharpe ratio, benchmark comparisons) and financial insights will be integrated with your portfolios.
        </CardDescription>

        <div className="mx-auto grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-3 text-left mb-6">
          <div className="rounded-lg border border-theme-border bg-theme-surface p-4">
            <div className="flex items-center gap-2 text-theme-primary text-xs font-semibold uppercase tracking-wider mb-1">
              <LineChart className="h-4 w-4" /> Performance
            </div>
            <p className="text-xs text-theme-text-muted">CAGR, XIRR, drawdown analysis, and historical return curves.</p>
          </div>

          <div className="rounded-lg border border-theme-border bg-theme-surface p-4">
            <div className="flex items-center gap-2 text-theme-primary text-xs font-semibold uppercase tracking-wider mb-1">
              <Cpu className="h-4 w-4" /> Risk Engine
            </div>
            <p className="text-xs text-theme-text-muted">Asset correlation matrices, volatility indexing, and risk scores.</p>
          </div>

          <div className="rounded-lg border border-theme-border bg-theme-surface p-4">
            <div className="flex items-center gap-2 text-theme-accent text-xs font-semibold uppercase tracking-wider mb-1">
              <Sparkles className="h-4 w-4" /> AI Insights
            </div>
            <p className="text-xs text-theme-text-muted">Portfolio summaries, expense ratio reviews, and asset allocation tips.</p>
          </div>
        </div>

        <Link to="/dashboard">
          <Button variant="outline" rightIcon={<ArrowRight className="h-4 w-4" />}>
            Back to Dashboard
          </Button>
        </Link>
      </Card>
    </div>
  );
};
