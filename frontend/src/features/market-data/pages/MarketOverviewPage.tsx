import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Globe,
  PlusCircle,
  RefreshCw,
  TrendingUp,
  ClipboardList,
  FileQuestion,
  AlertCircle,
} from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { DemoBadge } from '../components/DemoBadge';
import { InstrumentSearch } from '../components/InstrumentSearch';
import { QuoteCard } from '../components/QuoteCard';
import { PriceChart } from '../components/PriceChart';
import { OperatorWorklistPanel } from '../components/OperatorWorklistPanel';
import { InstrumentRequestsQueue } from '../components/InstrumentRequestsQueue';
import { useMarketHistory } from '../hooks/useMarketHistory';
import { useMarketOverview } from '../hooks/useMarketOverview';
import { Instrument, MarketQuote } from '../types';
import { Button } from '@/shared/ui/Button';

export const MarketOverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'OVERVIEW' | 'WORKLIST' | 'REQUESTS'>('OVERVIEW');
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument | null>(null);
  const [selectedRange, setSelectedRange] = useState<string>('1M');
  const [activeTab, setActiveTab] = useState<'EQUITY' | 'MUTUAL_FUND' | 'CRYPTO'>('EQUITY');

  // TanStack Query for Market Overview (5m staleTime, 30m gcTime)
  const {
    data: overview,
    isLoading: isLoadingOverview,
    isError: isOverviewError,
    error: overviewError,
    refetch: refetchOverview,
  } = useMarketOverview();

  // TanStack Query caching for historical timeseries chart (1h staleTime, 24h gcTime)
  const { data: historyResponse, isLoading: isLoadingHistory } = useMarketHistory({
    instrumentId: selectedInstrument?.id || '',
    range: selectedRange,
    priceType: selectedInstrument?.asset_class === 'MUTUAL_FUND'
      ? 'NAV'
      : selectedInstrument?.asset_class === 'INDEX'
        ? 'CLOSE'
        : selectedInstrument?.asset_class === 'COMMODITY'
          ? 'INDICATIVE_VALUATION'
          : 'LTP',
    enabled: Boolean(selectedInstrument?.id),
  });
  const historyPoints = historyResponse?.points ?? [];

  // Auto-select first equity index or stock if none selected
  useEffect(() => {
    if (!selectedInstrument && overview?.equities && overview.equities.length > 0) {
      const firstId = overview.equities[0].id;
      marketDataApi.getInstrument(firstId).then(setSelectedInstrument).catch(() => {});
    }
  }, [overview, selectedInstrument]);

  const handleSelectFromSearch = async (inst: Instrument) => {
    try {
      const full = await marketDataApi.getInstrument(inst.id);
      setSelectedInstrument(full);
    } catch {
      setSelectedInstrument(inst);
    }
  };

  const handleSelectOverviewItem = async (itemId: string) => {
    try {
      const full = await marketDataApi.getInstrument(itemId);
      setSelectedInstrument(full);
    } catch (err) {
      console.error('Failed to fetch instrument:', err);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Demo Notice Banner */}
      <DemoBadge isBanner className="shadow-sm" />

      {/* Header & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text flex items-center gap-2">
            <Globe className="h-7 w-7 text-theme-primary" />
            Market Intelligence
          </h1>
          <p className="text-sm text-theme-text-muted mt-1">
            Indian financial markets, benchmark indices, equities, mutual funds, and cryptocurrencies.
          </p>
        </div>

        <div className="w-full md:w-96">
          <InstrumentSearch onSelect={handleSelectFromSearch} />
        </div>
      </div>

      {/* View Mode Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-theme-border pb-3">
        <button
          onClick={() => setViewMode('OVERVIEW')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            viewMode === 'OVERVIEW'
              ? 'bg-theme-primary text-white shadow-sm'
              : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
          }`}
        >
          <TrendingUp className="h-3.5 w-3.5" />
          Market Overview
        </button>

        <button
          onClick={() => setViewMode('WORKLIST')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            viewMode === 'WORKLIST'
              ? 'bg-theme-primary text-white shadow-sm'
              : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
          }`}
        >
          <ClipboardList className="h-3.5 w-3.5" />
          Collection Worklist
        </button>

        <button
          onClick={() => setViewMode('REQUESTS')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
            viewMode === 'REQUESTS'
              ? 'bg-theme-primary text-white shadow-sm'
              : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
          }`}
        >
          <FileQuestion className="h-3.5 w-3.5" />
          Instrument Requests
        </button>
      </div>

      {viewMode === 'WORKLIST' && <OperatorWorklistPanel />}
      {viewMode === 'REQUESTS' && <InstrumentRequestsQueue />}

      {viewMode === 'OVERVIEW' && (
        <>
          {/* Error Banner */}
          {isOverviewError && (
            <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-400 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>Failed to load market overview: {String(overviewError)}</span>
              </div>
              <button
                onClick={() => refetchOverview()}
                className="underline hover:text-rose-300 font-semibold"
              >
                Retry
              </button>
            </div>
          )}

          {/* Benchmark Indices Row */}
          {overview?.indices && overview.indices.length > 0 && (
            <section aria-labelledby="indices-heading">
              <div className="flex items-center justify-between mb-3">
                <h2 id="indices-heading" className="text-xs font-bold uppercase tracking-wider text-theme-text-muted">
                  Benchmark Indices
                </h2>
                <button
                  onClick={() => refetchOverview()}
                  disabled={isLoadingOverview}
                  className="flex items-center gap-1.5 text-xs text-theme-primary hover:underline font-medium"
                >
                  <RefreshCw className={`h-3 w-3 ${isLoadingOverview ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {overview.indices.map((idx) => {
                  const quote: MarketQuote = {
                    symbol: idx.symbol,
                    price: idx.price,
                    change_amount: idx.change_amount,
                    change_percent: idx.change_percent,
                    provider: 'DEMO',
                    is_synthetic: idx.is_synthetic,
                    currency: 'INR',
                    timestamp: idx.timestamp,
                  };
                  return (
                    <QuoteCard
                      key={idx.id}
                      symbol={idx.symbol}
                      name={idx.name}
                      exchange={idx.exchange}
                      quote={quote}
                      onSelect={() => handleSelectOverviewItem(idx.id)}
                      className={selectedInstrument?.id === idx.id ? 'ring-2 ring-theme-primary border-transparent' : ''}
                    />
                  );
                })}
              </div>
            </section>
          )}

          {/* Main Grid: Left = Assets Explorer, Right = Selected Instrument Chart & Details */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Asset Lists (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center gap-2 border-b border-theme-border pb-2">
                <button
                  onClick={() => setActiveTab('EQUITY')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                    activeTab === 'EQUITY'
                      ? 'bg-theme-primary text-theme-text-inverse'
                      : 'text-theme-text-muted hover:text-theme-text'
                  }`}
                >
                  Equities & Stocks
                </button>
                <button
                  onClick={() => setActiveTab('MUTUAL_FUND')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                    activeTab === 'MUTUAL_FUND'
                      ? 'bg-theme-primary text-theme-text-inverse'
                      : 'text-theme-text-muted hover:text-theme-text'
                  }`}
                >
                  Mutual Funds
                </button>
                <button
                  onClick={() => setActiveTab('CRYPTO')}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                    activeTab === 'CRYPTO'
                      ? 'bg-theme-primary text-theme-text-inverse'
                      : 'text-theme-text-muted hover:text-theme-text'
                  }`}
                >
                  Cryptocurrencies
                </button>
              </div>

              <div className="space-y-3">
                {isLoadingOverview && !overview && (
                  <div className="p-8 text-center text-xs text-theme-text-muted animate-pulse">
                    Loading market overview...
                  </div>
                )}

                {activeTab === 'EQUITY' &&
                  overview?.equities?.map((item) => {
                    const quote: MarketQuote = {
                      symbol: item.symbol,
                      price: item.price,
                      change_amount: item.change_amount,
                      change_percent: item.change_percent,
                      provider: 'DEMO',
                      is_synthetic: item.is_synthetic,
                      currency: 'INR',
                      timestamp: item.timestamp,
                    };
                    return (
                      <QuoteCard
                        key={item.id}
                        symbol={item.symbol}
                        name={item.name}
                        exchange={item.exchange}
                        quote={quote}
                        onSelect={() => handleSelectOverviewItem(item.id)}
                        className={selectedInstrument?.id === item.id ? 'ring-2 ring-theme-primary border-transparent' : ''}
                      />
                    );
                  })}

                {activeTab === 'MUTUAL_FUND' &&
                  (overview?.mutual_funds && overview.mutual_funds.length > 0 ? (
                    overview.mutual_funds.map((item) => {
                      const quote: MarketQuote = {
                        symbol: item.symbol,
                        price: item.price,
                        change_amount: item.change_amount,
                        change_percent: item.change_percent,
                        provider: 'MFAPI',
                        is_synthetic: item.is_synthetic,
                        currency: 'INR',
                        timestamp: item.timestamp,
                      };
                      return (
                        <QuoteCard
                          key={item.id}
                          symbol={item.symbol}
                          name={item.name}
                          exchange="AMFI"
                          quote={quote}
                          fundHouse={item.fund_house}
                          planType={item.plan_type}
                          optionType={item.option_type}
                          onSelect={() => handleSelectOverviewItem(item.id)}
                          className={selectedInstrument?.id === item.id ? 'ring-2 ring-theme-primary border-transparent' : ''}
                        />
                      );
                    })
                  ) : (
                    <div className="p-4 text-xs text-theme-text-muted text-center border border-dashed border-theme-border rounded-xl">
                      No mutual fund instruments loaded.
                    </div>
                  ))}

                {activeTab === 'CRYPTO' &&
                  (overview?.cryptocurrencies && overview.cryptocurrencies.length > 0 ? (
                    overview.cryptocurrencies.map((item) => {
                      const quote: MarketQuote = {
                        symbol: item.symbol,
                        price: item.price,
                        change_amount: item.change_amount,
                        change_percent: item.change_percent,
                        provider: 'COINGECKO',
                        is_synthetic: item.is_synthetic,
                        currency: 'INR',
                        timestamp: item.timestamp,
                      };
                      return (
                        <QuoteCard
                          key={item.id}
                          symbol={item.symbol}
                          name={item.name}
                          exchange="CRYPTO"
                          quote={quote}
                          marketCap={item.market_cap}
                          volume24h={item.volume_24h}
                          onSelect={() => handleSelectOverviewItem(item.id)}
                          className={selectedInstrument?.id === item.id ? 'ring-2 ring-theme-primary border-transparent' : ''}
                        />
                      );
                    })
                  ) : (
                    <div className="p-4 text-xs text-theme-text-muted text-center border border-dashed border-theme-border rounded-xl">
                      No cryptocurrency instruments loaded.
                    </div>
                  ))}
              </div>
            </div>

            {/* Right Column: Chart & Deep Dive Details (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              {selectedInstrument ? (
                <>
                  {historyPoints.some((point) => point.is_synthetic) && (
                    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                      Synthetic development data is displayed for demonstration only. It is not eligible for portfolio valuation.
                    </div>
                  )}

                  {/* Interactive Price Chart */}
                  <PriceChart
                    points={historyPoints}
                    symbol={selectedInstrument.symbol}
                    currency={selectedInstrument.currency}
                    selectedRange={selectedRange}
                    onRangeChange={setSelectedRange}
                    isLoading={isLoadingHistory}
                  />

                  {/* Instrument Details & Quick Actions */}
                  <div className="p-5 rounded-2xl border border-theme-border bg-theme-surface space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-theme-border/60 pb-3">
                      <div>
                        <h2 className="text-lg font-bold text-theme-text tracking-tight">
                          {selectedInstrument.name}
                        </h2>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-theme-bg text-theme-text-muted border border-theme-border uppercase">
                            {selectedInstrument.symbol}
                          </span>
                          {selectedInstrument.exchange && (
                            <span className="text-xs font-medium text-theme-text-muted">
                              Exchange: {selectedInstrument.exchange}
                            </span>
                          )}
                          {selectedInstrument.reference_data?.sector && (
                            <span className="text-xs text-theme-text-muted">
                              • {selectedInstrument.reference_data.sector}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Add to Portfolio Button */}
                      <Button
                        onClick={() => {
                          const category =
                            selectedInstrument.asset_class === 'MUTUAL_FUND'
                              ? 'mutual_funds'
                              : selectedInstrument.asset_class === 'COMMODITY'
                              ? 'gold'
                              : selectedInstrument.asset_class === 'CRYPTO'
                              ? 'crypto'
                              : 'equity';
                          const type =
                            selectedInstrument.asset_class === 'MUTUAL_FUND'
                              ? 'mutual_fund'
                              : selectedInstrument.asset_class === 'COMMODITY'
                              ? 'physical_gold'
                              : selectedInstrument.asset_class === 'CRYPTO'
                              ? 'crypto'
                              : 'listed_stock';
                          const query = new URLSearchParams({
                            category,
                            type,
                            symbol: selectedInstrument.symbol,
                            name: selectedInstrument.name,
                            instrument_id: selectedInstrument.id,
                          });
                          navigate(`/investments/new?${query.toString()}`);
                        }}
                        className="flex items-center gap-2 shrink-0"
                      >
                        <PlusCircle className="h-4 w-4" />
                        <span>Add to Portfolio</span>
                      </Button>
                    </div>

                    {/* Reference Attributes Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                      <div className="p-2.5 rounded-lg bg-theme-bg/60 border border-theme-border/40">
                        <span className="text-theme-text-muted block">Asset Class</span>
                        <span className="font-semibold text-theme-text">{selectedInstrument.asset_class}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-theme-bg/60 border border-theme-border/40">
                        <span className="text-theme-text-muted block">ISIN / Scheme Code</span>
                        <span className="font-semibold text-theme-text">
                          {selectedInstrument.isin || selectedInstrument.scheme_code || '—'}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-theme-bg/60 border border-theme-border/40">
                        <span className="text-theme-text-muted block">Market Cap Tier</span>
                        <span className="font-semibold text-theme-text">
                          {selectedInstrument.reference_data?.market_cap_category || '—'}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-theme-bg/60 border border-theme-border/40">
                        <span className="text-theme-text-muted block">Industry</span>
                        <span className="font-semibold text-theme-text">
                          {selectedInstrument.reference_data?.industry || '—'}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-theme-bg/60 border border-theme-border/40">
                        <span className="text-theme-text-muted block">Lot Size / Tick</span>
                        <span className="font-semibold text-theme-text">
                          {selectedInstrument.reference_data?.lot_size || 1} / ₹
                          {selectedInstrument.reference_data?.tick_size || '0.05'}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-theme-bg/60 border border-theme-border/40">
                        <span className="text-theme-text-muted block">Data Provider</span>
                        <span className="font-semibold text-theme-text">
                          {selectedInstrument.latest_quote?.provider || 'DEMO'}
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-12 text-center rounded-2xl border border-dashed border-theme-border text-theme-text-muted">
                  Select an instrument to view its historical chart and reference metrics.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
