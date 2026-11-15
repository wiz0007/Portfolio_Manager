import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layers,
  Plus,
  Eye,
  Edit2,
  Trash2,
  TrendingUp,
  TrendingDown,
  AlertCircle,
} from 'lucide-react';
import { InvestmentListItem } from '../../types/investmentApiTypes';
import { useDeleteInvestment } from '../../hooks/useInvestments';
import { InvestmentDetailModal } from '../InvestmentDetailModal/InvestmentDetailModal';
import { InvestmentEditModal } from '../InvestmentEditModal/InvestmentEditModal';
import { Button } from '@/shared/ui/Button';

export interface HoldingsListProps {
  portfolioId: string;
  baseCurrency: string;
  investments: InvestmentListItem[];
  isLoading?: boolean;
}

const CATEGORY_FILTERS = [
  { id: 'all', label: 'All Assets' },
  { id: 'cash', label: 'Cash & Bank' },
  { id: 'fixed_income', label: 'Fixed Income' },
  { id: 'equity', label: 'Equities' },
  { id: 'mutual_funds', label: 'Mutual Funds' },
  { id: 'gold', label: 'Gold' },
  { id: 'real_estate', label: 'Real Estate' },
  { id: 'crypto', label: 'Crypto' },
];

export const HoldingsList: React.FC<HoldingsListProps> = ({
  portfolioId,
  baseCurrency,
  investments,
  isLoading = false,
}) => {
  const navigate = useNavigate();
  const deleteMutation = useDeleteInvestment(portfolioId);

  const [selectedCategory, setSelectedCategory] = useState('all');
  const [detailInvestmentId, setDetailInvestmentId] = useState<string | null>(null);
  const [editInvestmentId, setEditInvestmentId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<InvestmentListItem | null>(null);

  // Filtered investments
  const filteredInvestments = useMemo(() => {
    if (selectedCategory === 'all') return investments;
    return investments.filter((inv) => inv.category === selectedCategory);
  }, [investments, selectedCategory]);

  // Aggregate stats
  const { totalInitial, totalCurrent, netGain, netGainPct } = useMemo(() => {
    let initialSum = 0;
    let currentSum = 0;
    investments.forEach((inv) => {
      initialSum += Number(inv.initial_value || 0);
      currentSum += Number(inv.current_value || 0);
    });
    const gain = currentSum - initialSum;
    const pct = initialSum > 0 ? (gain / initialSum) * 100 : 0;
    return {
      totalInitial: initialSum,
      totalCurrent: currentSum,
      netGain: gain,
      netGainPct: pct,
    };
  }, [investments]);

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      setDeleteTarget(null);
    } catch (err) {
      console.error('Failed to delete investment holding:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center text-sm text-theme-text-muted">
        Loading portfolio holdings...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Metric Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-theme-text-muted">
            Total Holdings
          </span>
          <div className="text-2xl font-bold text-theme-text mt-1">{investments.length}</div>
          <span className="text-[11px] text-theme-text-muted mt-0.5 block">
            Across {new Set(investments.map((i) => i.category)).size} asset categories
          </span>
        </div>

        <div className="p-5 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-theme-text-muted">
            Capital Invested
          </span>
          <div className="text-2xl font-bold text-theme-text mt-1">
            {baseCurrency} {totalInitial.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-theme-text-muted mt-0.5 block">Total cost outlay</span>
        </div>

        <div className="p-5 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-theme-text-muted">
            Current Valuation
          </span>
          <div className="text-2xl font-bold text-theme-text mt-1">
            {baseCurrency} {totalCurrent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-theme-text-muted mt-0.5 block">Latest market/cost balance</span>
        </div>

        <div className="p-5 rounded-xl bg-theme-card border border-theme-border shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-theme-text-muted">
            Net Unrealized Return
          </span>
          <div
            className={`text-2xl font-bold mt-1 flex items-center gap-1.5 ${
              netGain >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {netGain >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
            {netGain >= 0 ? '+' : ''}
            {baseCurrency} {Math.abs(netGain).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-theme-text-muted mt-0.5 block">
            {netGainPct.toFixed(2)}% overall return
          </span>
        </div>
      </div>

      {/* Filter Tabs & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          {CATEGORY_FILTERS.map((cat) => {
            const count =
              cat.id === 'all'
                ? investments.length
                : investments.filter((i) => i.category === cat.id).length;
            const isSelected = selectedCategory === cat.id;

            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-colors flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-theme-primary text-white shadow-sm'
                    : 'bg-theme-card text-theme-text-muted hover:text-theme-text hover:bg-theme-hover border border-theme-border'
                }`}
              >
                <span>{cat.label}</span>
                {count > 0 && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-semibold ${
                      isSelected ? 'bg-white/20 text-white' : 'bg-theme-surface text-theme-text-muted'
                    }`}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <Button
          onClick={() => navigate(`/investments/new?portfolioId=${portfolioId}`)}
          variant="primary"
          size="sm"
          className="shrink-0 self-start sm:self-auto"
        >
          <Plus className="mr-1.5 h-3.5 w-3.5" /> Record Investment
        </Button>
      </div>

      {/* Holdings List / Empty State */}
      {filteredInvestments.length === 0 ? (
        <div className="border border-theme-border border-dashed rounded-2xl p-12 text-center bg-theme-card/30 space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-theme-surface text-theme-text-muted border border-theme-border">
            <Layers className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-theme-text">No Holdings Found</h3>
          <p className="mx-auto max-w-md text-xs text-theme-text-muted leading-relaxed">
            {investments.length === 0
              ? 'This portfolio has no recorded investments yet. Add bank deposits, equities, real estate, gold, bonds, or crypto.'
              : `No investments match the selected filter "${selectedCategory}".`}
          </p>
          <div className="pt-2">
            <Button
              onClick={() => navigate(`/investments/new?portfolioId=${portfolioId}`)}
              variant="primary"
              size="sm"
            >
              <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Investment Holding
            </Button>
          </div>
        </div>
      ) : (
        <div className="border border-theme-border rounded-xl bg-theme-card overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-theme-surface border-b border-theme-border text-xs uppercase tracking-wider text-theme-text-muted font-semibold">
                <tr>
                  <th className="px-5 py-3.5">Asset / Holding</th>
                  <th className="px-4 py-3.5">Category</th>
                  <th className="px-4 py-3.5 text-right">Cost Outlay</th>
                  <th className="px-4 py-3.5 text-right">Current Value</th>
                  <th className="px-4 py-3.5 text-right">Unrealized P&amp;L</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border">
                {filteredInvestments.map((inv) => {
                  const initial = Number(inv.initial_value || 0);
                  const current = Number(inv.current_value || 0);
                  const diff = current - initial;
                  const diffPct = initial > 0 ? (diff / initial) * 100 : 0;

                  return (
                    <tr
                      key={inv.id}
                      className="hover:bg-theme-surface/50 transition-colors group"
                    >
                      <td className="px-5 py-4">
                        <div className="font-semibold text-theme-text group-hover:text-theme-primary transition-colors">
                          {inv.display_name}
                        </div>
                        <div className="text-xs text-theme-text-muted capitalize">
                          {inv.asset_type.replace(/_/g, ' ')}
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-theme-primary/10 text-theme-primary border border-theme-primary/20 uppercase tracking-wide">
                          {inv.category.replace(/_/g, ' ')}
                        </span>
                      </td>

                      <td className="px-4 py-4 text-right font-mono text-xs text-theme-text-secondary">
                        {inv.currency} {initial.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>

                      <td className="px-4 py-4 text-right font-mono text-xs font-semibold text-theme-text">
                        {inv.currency} {current.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>

                      <td className="px-4 py-4 text-right">
                        <div
                          className={`font-mono text-xs font-semibold ${
                            diff >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {diff >= 0 ? '+' : ''}
                          {inv.currency} {diff.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[11px] text-theme-text-muted font-mono">
                          {diffPct >= 0 ? '+' : ''}
                          {diffPct.toFixed(2)}%
                        </div>
                      </td>

                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setDetailInvestmentId(inv.id)}
                            title="View holding specifications"
                            className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setEditInvestmentId(inv.id)}
                            title="Edit holding"
                            className="p-1.5 rounded-lg text-theme-text-muted hover:text-theme-text hover:bg-theme-hover transition-colors"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setDeleteTarget(inv)}
                            title="Delete holding"
                            className="p-1.5 rounded-lg text-theme-text-muted hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {detailInvestmentId && (
        <InvestmentDetailModal
          portfolioId={portfolioId}
          investmentId={detailInvestmentId}
          onClose={() => setDetailInvestmentId(null)}
          onEdit={() => {
            const id = detailInvestmentId;
            setDetailInvestmentId(null);
            setEditInvestmentId(id);
          }}
        />
      )}

      {/* Edit Modal */}
      {editInvestmentId && (
        <InvestmentEditModal
          portfolioId={portfolioId}
          investmentId={editInvestmentId}
          onClose={() => setEditInvestmentId(null)}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-holding-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        >
          <div className="relative w-full max-w-md bg-theme-surface border border-theme-border rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="h-10 w-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center shrink-0">
                <AlertCircle className="h-5 w-5" />
              </div>
              <h3 id="delete-holding-title" className="text-base font-bold text-theme-text">
                Delete Investment Holding?
              </h3>
            </div>
            <p className="text-xs text-theme-text-muted leading-relaxed">
              Are you sure you want to delete{' '}
              <strong className="text-theme-text">{deleteTarget.display_name}</strong>? This will permanently
              remove the holding record, its child details, ledger transactions, and historical valuations.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeleteTarget(null)}
                disabled={deleteMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteConfirm}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete Holding'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
