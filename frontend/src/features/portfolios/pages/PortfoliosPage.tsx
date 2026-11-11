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
          <h1 className="text-2xl font-bold tracking-tight text-white">Portfolios</h1>
          <p className="text-sm text-slate-400 mt-1">
            Create and manage independent investment containers and currency allocations.
          </p>
        </div>
        <Button
          onClick={() => navigate('/portfolios/new')}
          className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0"
        >
          <Plus className="mr-2 h-4 w-4" /> Create Portfolio
        </Button>
      </div>

      {/* Filter / Search Bar */}
      {portfolios.length > 0 && (
        <div className="flex items-center gap-3 max-w-md">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              type="text"
              placeholder="Filter by name, currency, or note..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-900/60 border-slate-800 text-white text-sm"
            />
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="py-16 flex flex-col items-center justify-center text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500 mb-2" />
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
        <Card className="border-slate-800 bg-slate-900/40 border-dashed p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 mb-4">
            <Briefcase className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-semibold text-white">No Portfolios Found</h3>
          <p className="mx-auto max-w-md text-sm text-slate-400 mt-2 mb-6">
            You haven't created any portfolios yet. Create your first portfolio to organize your assets, holdings, and currencies.
          </p>
          <Button
            onClick={() => navigate('/portfolios/new')}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Plus className="mr-2 h-4 w-4" /> Create Your First Portfolio
          </Button>
        </Card>
      )}

      {/* Portfolio Grid */}
      {!isLoading && !isError && portfolios.length > 0 && (
        <>
          {filteredPortfolios.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              No portfolios match "{searchQuery}".
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredPortfolios.map((portfolio) => (
                <Card
                  key={portfolio.id}
                  className="border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all flex flex-col justify-between p-5 group"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <Link
                          to={`/portfolios/${portfolio.id}`}
                          className="text-base font-semibold text-white group-hover:text-indigo-400 transition-colors truncate block"
                          title={portfolio.name}
                        >
                          {portfolio.name}
                        </Link>
                        <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                          <Calendar className="h-3.5 w-3.5" />
                          <span>Created {formatDate(portfolio.created_at)}</span>
                        </div>
                      </div>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0 font-mono">
                        {portfolio.base_currency}
                      </span>
                    </div>

                    {portfolio.description ? (
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {portfolio.description}
                      </p>
                    ) : (
                      <p className="text-xs text-slate-600 italic">No description provided.</p>
                    )}
                  </div>

                  {/* Actions footer */}
                  <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
                    <Link
                      to={`/portfolios/${portfolio.id}`}
                      className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-medium"
                    >
                      View Details <ExternalLink className="h-3 w-3" />
                    </Link>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/portfolios/${portfolio.id}/edit`)}
                        className="h-8 w-8 p-0 text-slate-400 hover:text-indigo-400"
                        title="Edit portfolio"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeletingPortfolio(portfolio)}
                        className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <Card className="w-full max-w-md border-slate-800 bg-slate-900 p-6 space-y-4 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center shrink-0">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Delete Portfolio</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Are you sure you want to delete{' '}
                  <span className="font-semibold text-white">"{deletingPortfolio.name}"</span>?
                  This action cannot be undone.
                </p>
              </div>
            </div>

            {deleteError && (
              <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded p-2.5">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeletingPortfolio(null)}
                disabled={isDeleting}
                className="border-slate-700 text-slate-300"
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={confirmDelete}
                disabled={isDeleting}
                className="bg-rose-600 hover:bg-rose-700 text-white"
              >
                {isDeleting ? 'Deleting...' : 'Delete Portfolio'}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
