import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Briefcase,
  Plus,
  Trash2,
  Edit2,
  ExternalLink,
  Search,
  Calendar,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { usePortfolios, useDeletePortfolio } from '../hooks/usePortfolios';
import { Portfolio } from '../types';
import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';

export const PortfoliosPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: portfolios = [], isLoading, isError } = usePortfolios();
  const { mutate: deletePortfolio, isPending: isDeleting } = useDeletePortfolio();

  const [searchQuery, setSearchQuery] = useState('');
  const [deletingPortfolio, setDeletingPortfolio] = useState<Portfolio | null>(null);
  const [deleteError, setDeleteError] = useState('');

  const filteredPortfolios = portfolios.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.base_currency.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const confirmDelete = () => {
    if (!deletingPortfolio) return;
    setDeleteError('');
    deletePortfolio(deletingPortfolio.id, {
      onSuccess: () => {
        setDeletingPortfolio(null);
      },
      onError: (err: any) => {
        setDeleteError(err?.message || 'Failed to delete portfolio. Please try again.');
      },
    });
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-theme-text">Portfolios</h1>
          <p className="text-sm text-theme-text-muted mt-1">
            Create and manage independent investment containers and currency allocations.
          </p>
        </div>
        <Button
          onClick={() => navigate('/portfolios/new')}
          className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shrink-0 shadow-sm"
        >
          <Plus className="mr-2 h-4 w-4" /> Create Portfolio
        </Button>
      </div>

      {/* Filter / Search Bar */}
      {portfolios.length > 0 && (
        <div className="flex items-center gap-3 max-w-md">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-theme-text-muted" />
            <Input
              type="text"
              placeholder="Filter by name, currency, or note..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-theme-surface border-theme-border text-theme-text text-sm"
            />
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="py-16 flex flex-col items-center justify-center text-theme-text-muted">
          <Loader2 className="h-8 w-8 animate-spin text-theme-primary mb-2" />
          <p className="text-sm">Loading your portfolios...</p>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <Card className="border-rose-900/40 bg-rose-950/10 p-6 text-center text-rose-300">
          <AlertTriangle className="h-8 w-8 text-rose-400 mx-auto mb-2" />
          <h3 className="text-base font-semibold text-rose-200">Unable to load portfolios</h3>
          <p className="text-xs text-rose-400/80 mt-1">
            A network error occurred while connecting to the backend.
          </p>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && portfolios.length === 0 && (
        <Card className="border-theme-border bg-theme-card/60 border-dashed p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-theme-primary-subtle text-theme-primary border border-theme-primary/30 mb-4">
            <Briefcase className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-semibold text-theme-text">No Portfolios Found</h3>
          <p className="mx-auto max-w-md text-sm text-theme-text-muted mt-2 mb-6">
            You haven't created any portfolios yet. Create your first portfolio to organize your assets, holdings, and currencies.
          </p>
          <Button
            onClick={() => navigate('/portfolios/new')}
            className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm"
          >
            <Plus className="mr-2 h-4 w-4" /> Create Your First Portfolio
          </Button>
        </Card>
      )}

      {/* Portfolio Grid */}
      {!isLoading && !isError && portfolios.length > 0 && (
        <>
          {filteredPortfolios.length === 0 ? (
            <div className="text-center py-12 text-theme-text-muted text-sm">
              No portfolios match "{searchQuery}".
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredPortfolios.map((portfolio) => (
                <Card
                  key={portfolio.id}
                  className="border-theme-border bg-theme-card hover:border-theme-primary/50 transition-all flex flex-col justify-between p-5 group shadow-sm"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <Link
                          to={`/portfolios/${portfolio.id}`}
                          className="text-base font-semibold text-theme-text group-hover:text-theme-primary transition-colors truncate block"
                          title={portfolio.name}
                        >
                          {portfolio.name}
                        </Link>
                        <div className="flex items-center gap-2 mt-1 text-xs text-theme-text-muted">
                          <Calendar className="h-3.5 w-3.5" />
                          <span>Created {formatDate(portfolio.created_at)}</span>
                        </div>
                      </div>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-theme-primary-subtle text-theme-primary border border-theme-primary/20 shrink-0 font-mono">
                        {portfolio.base_currency}
                      </span>
                    </div>

                    {portfolio.description ? (
                      <p className="text-xs text-theme-text-secondary line-clamp-2 leading-relaxed">
                        {portfolio.description}
                      </p>
                    ) : (
                      <p className="text-xs text-theme-text-muted italic">No description provided.</p>
                    )}
                  </div>

                  {/* Actions footer */}
                  <div className="pt-4 mt-4 border-t border-theme-border flex items-center justify-between">
                    <Link
                      to={`/portfolios/${portfolio.id}`}
                      className="text-xs text-theme-text-muted hover:text-theme-text flex items-center gap-1 font-medium transition-colors"
                    >
                      View Details <ExternalLink className="h-3 w-3" />
                    </Link>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/portfolios/${portfolio.id}/edit`)}
                        className="h-8 w-8 p-0 text-theme-text-muted hover:text-theme-primary"
                        title="Edit portfolio"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeletingPortfolio(portfolio)}
                        className="h-8 w-8 p-0 text-theme-text-muted hover:text-theme-negative"
                        title="Delete portfolio"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation Modal */}
      {deletingPortfolio && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-theme-bg/80 backdrop-blur-sm">
          <Card className="w-full max-w-md border-theme-border bg-theme-card p-6 space-y-4 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center shrink-0">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-base font-semibold text-theme-text">Delete Portfolio</h3>
                <p className="text-xs text-theme-text-muted mt-1 leading-relaxed">
                  Are you sure you want to delete <span className="font-semibold text-theme-text">"{deletingPortfolio.name}"</span>?
                  This action cannot be undone.
                </p>
              </div>
            </div>

            {deleteError && (
              <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/30 text-rose-300 text-xs">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeletingPortfolio(null)}
                disabled={isDeleting}
                className="text-theme-text border-theme-border hover:bg-theme-hover"
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={confirmDelete}
                isLoading={isDeleting}
              >
                Delete
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
