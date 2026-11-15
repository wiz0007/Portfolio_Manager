import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Plus, Check } from 'lucide-react';
import { Portfolio } from '@/features/portfolios/types';
import { Button } from '@/shared/ui/Button';
import styles from './PortfolioSelector.module.css';

export interface PortfolioSelectorProps {
  portfolios: Portfolio[];
  selectedPortfolioId?: string;
  onSelectPortfolio: (portfolio: Portfolio) => void;
  isLoading?: boolean;
}

export const PortfolioSelector: React.FC<PortfolioSelectorProps> = ({
  portfolios,
  selectedPortfolioId,
  onSelectPortfolio,
  isLoading = false,
}) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.title}>Loading portfolios...</div>
        </div>
      </div>
    );
  }

  if (portfolios.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Choose Destination Portfolio</h2>
          <p className={styles.description}>
            Every investment must belong to a verified portfolio container.
          </p>
        </div>
        <div className={styles.emptyState}>
          <Briefcase className={styles.emptyIcon} size={40} />
          <p className={styles.emptyText}>
            You haven't created any portfolios yet. Please create a portfolio first before adding investments.
          </p>
          <Button variant="primary" onClick={() => navigate('/portfolios/new')}>
            <Plus size={16} />
            Create Your First Portfolio
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Select Destination Portfolio</h2>
        <p className={styles.description}>
          Choose the portfolio container where this investment holding will be recorded.
        </p>
      </div>

      <div className={styles.grid}>
        {portfolios.map((portfolio) => {
          const isSelected = selectedPortfolioId === portfolio.id;
          return (
            <div
              key={portfolio.id}
              role="button"
              tabIndex={0}
              className={`${styles.portfolioCard} ${isSelected ? styles.selectedCard : ''}`}
              onClick={() => onSelectPortfolio(portfolio)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectPortfolio(portfolio);
                }
              }}
            >
              <div className={styles.cardHeader}>
                <div className={styles.cardIcon}>
                  <Briefcase size={18} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className={styles.currencyBadge}>{portfolio.base_currency}</span>
                  {isSelected && <Check size={16} color="var(--color-primary)" />}
                </div>
              </div>
              <h3 className={styles.portfolioName}>{portfolio.name}</h3>
              {portfolio.description && (
                <p className={styles.portfolioDesc}>{portfolio.description}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
