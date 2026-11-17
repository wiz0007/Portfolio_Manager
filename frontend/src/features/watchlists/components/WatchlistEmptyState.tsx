import React from 'react';
import { Eye, Plus, Search } from 'lucide-react';
import { Button } from '@/shared/ui/Button';

interface WatchlistEmptyStateProps {
  onAddClick: () => void;
  isFiltered?: boolean;
  onClearFilter?: () => void;
}

export const WatchlistEmptyState: React.FC<WatchlistEmptyStateProps> = ({
  onAddClick,
  isFiltered = false,
  onClearFilter,
}) => {
  if (isFiltered) {
    return (
      <div className="rounded-2xl border border-dashed border-theme-border bg-theme-surface/50 p-12 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-theme-surface border border-theme-border text-theme-text-muted mb-4">
          <Search className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-theme-text mb-1">No matching watchlist items</h3>
        <p className="text-sm text-theme-text-muted max-w-sm mx-auto mb-6">
          No instruments in your watchlist match the current filter or search criteria.
        </p>
        {onClearFilter && (
          <Button variant="outline" size="sm" onClick={onClearFilter}>
            Clear Filters
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-dashed border-theme-border bg-theme-surface/40 p-12 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-theme-primary-subtle border border-theme-primary/30 text-theme-primary mb-4 shadow-sm">
        <Eye className="h-7 w-7" />
      </div>
      <h3 className="text-lg font-semibold text-theme-text mb-2">Your watchlist is empty</h3>
      <p className="text-sm text-theme-text-muted max-w-md mx-auto mb-6">
        Monitor equities, mutual funds, gold, and other instruments with verified market prices and freshness tracking before adding them to your portfolio.
      </p>
      <Button
        variant="primary"
        onClick={onAddClick}
        leftIcon={<Plus className="h-4 w-4" />}
      >
        Add Instrument to Watchlist
      </Button>
    </div>
  );
};
