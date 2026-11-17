import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, X, TrendingUp } from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { Instrument } from '../types';

import { InstrumentRequestModal } from './InstrumentRequestModal';

interface InstrumentSearchProps {
  onSelect: (instrument: Instrument) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export const InstrumentSearch: React.FC<InstrumentSearchProps> = ({
  onSelect,
  placeholder = 'Search stocks, mutual funds, indices (e.g. RELIANCE, TCS, NIFTY50)...',
  className = '',
  autoFocus = false,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Instrument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search effect
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsLoading(false);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    const handler = setTimeout(async () => {
      try {
        const data = await marketDataApi.searchInstruments(query.trim());
        setResults(data);
        setIsOpen(true);
        setSelectedIndex(-1);
      } catch (err) {
        console.error('Failed to search instruments:', err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 250);

    return () => clearTimeout(handler);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        handleSelect(results[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (instrument: Instrument) => {
    onSelect(instrument);
    setQuery('');
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-theme-text-muted pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-theme-border bg-theme-surface text-theme-text placeholder:text-theme-text-muted focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary text-sm transition-all"
        />
        {isLoading ? (
          <Loader2 className="absolute right-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-theme-text-muted animate-spin" />
        ) : query ? (
          <button
            onClick={() => {
              setQuery('');
              setResults([]);
              setIsOpen(false);
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-theme-text-muted hover:text-theme-text rounded-md"
            aria-label="Clear search"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>

      {/* Results Dropdown */}
      {isOpen && (
        <div className="absolute left-0 right-0 top-full mt-2 z-50 max-h-80 overflow-y-auto rounded-xl border border-theme-border bg-theme-surface/95 backdrop-blur shadow-xl divide-y divide-theme-border/50">
          {results.length > 0 ? (
            results.map((item, index) => {
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`px-4 py-3 flex items-center justify-between cursor-pointer transition-colors ${
                    isSelected ? 'bg-theme-hover' : 'hover:bg-theme-hover/60'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-theme-primary-subtle text-theme-primary shrink-0">
                      <TrendingUp className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-theme-text tracking-tight">
                          {item.symbol}
                        </span>
                        {item.exchange && (
                          <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-theme-bg text-theme-text-muted border border-theme-border uppercase">
                            {item.exchange}
                          </span>
                        )}
                        <span className="text-[10px] text-theme-text-muted uppercase">
                          {item.asset_class}
                        </span>
                      </div>
                      <div className="text-xs text-theme-text-muted truncate mt-0.5">
                        {item.name}
                      </div>
                    </div>
                  </div>

                  {item.latest_quote && (
                    <div className="text-right shrink-0 pl-3">
                      <div className="font-semibold text-sm text-theme-text">
                        ₹{parseFloat(item.latest_quote.price).toFixed(2)}
                      </div>
                      {item.latest_quote.change_percent && (
                        <div
                          className={`text-xs font-medium ${
                            parseFloat(item.latest_quote.change_percent) >= 0
                              ? 'text-emerald-400'
                              : 'text-rose-400'
                          }`}
                        >
                          {parseFloat(item.latest_quote.change_percent) >= 0 ? '+' : ''}
                          {parseFloat(item.latest_quote.change_percent).toFixed(2)}%
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="p-4 text-center text-sm text-theme-text-muted">
              <div>No matching instruments found for "{query}".</div>
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  setIsRequestModalOpen(true);
                }}
                className="mt-2 text-xs font-semibold text-theme-primary hover:underline focus:outline-none"
              >
                + Request unlisted instrument addition
              </button>
            </div>
          )}
        </div>
      )}

      <InstrumentRequestModal
        isOpen={isRequestModalOpen}
        onClose={() => setIsRequestModalOpen(false)}
        initialQuery={query}
      />
    </div>
  );
};
