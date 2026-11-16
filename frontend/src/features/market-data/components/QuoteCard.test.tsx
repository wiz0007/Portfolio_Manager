import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QuoteCard } from './QuoteCard';
import { MarketQuote } from '../types';

describe('QuoteCard', () => {
  const sampleQuote: MarketQuote = {
    symbol: 'RELIANCE',
    price: '1344.8000',
    open_price: '1330.0000',
    high_price: '1360.0000',
    low_price: '1325.0000',
    volume: 1250000,
    change_amount: '14.8000',
    change_percent: '1.1128',
    provider: 'DEMO',
    is_synthetic: true,
    currency: 'INR',
    timestamp: '2026-11-16T10:00:00Z',
  };

  it('renders symbol, formatted price, change percentage and demo badge for synthetic quotes', () => {
    render(
      <QuoteCard
        symbol="RELIANCE"
        name="Reliance Industries Ltd."
        exchange="NSE"
        quote={sampleQuote}
      />
    );

    expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getByText('Reliance Industries Ltd.')).toBeInTheDocument();
    expect(screen.getByText('NSE')).toBeInTheDocument();
    expect(screen.getByText(/1,344\.80/)).toBeInTheDocument();
    expect(screen.getByText('+1.11%')).toBeInTheDocument();
    expect(screen.getByText('DEMO DATA')).toBeInTheDocument();
  });

  it('handles negative price change display with minus sign', () => {
    const negativeQuote: MarketQuote = {
      ...sampleQuote,
      change_amount: '-25.5000',
      change_percent: '-1.8900',
    };

    render(
      <QuoteCard
        symbol="TCS"
        name="Tata Consultancy Services"
        exchange="NSE"
        quote={negativeQuote}
      />
    );

    expect(screen.getByText('-1.89%')).toBeInTheDocument();
  });

  it('calls onSelect when card is clicked', () => {
    const onSelect = vi.fn();
    render(
      <QuoteCard
        symbol="RELIANCE"
        quote={sampleQuote}
        onSelect={onSelect}
      />
    );

    fireEvent.click(screen.getByText('RELIANCE'));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });
});
