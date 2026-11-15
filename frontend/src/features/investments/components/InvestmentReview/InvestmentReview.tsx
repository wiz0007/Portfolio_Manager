import React from 'react';
import { Portfolio } from '@/features/portfolios/types';
import { AssetCategoryConfig, AssetTypeConfig } from '../../types/investmentTypes';
import { FormActions } from '@/shared/components/forms';
import styles from './InvestmentReview.module.css';

export interface InvestmentReviewProps {
  portfolio: Portfolio;
  category: AssetCategoryConfig;
  type: AssetTypeConfig;
  formData: Record<string, any>;
  onConfirm: () => void;
  onEdit: () => void;
  isSubmitting?: boolean;
}

export const InvestmentReview: React.FC<InvestmentReviewProps> = ({
  portfolio,
  category,
  type,
  formData,
  onConfirm,
  onEdit,
  isSubmitting = false,
}) => {
  // Extract key primary title
  const primaryName =
    formData.account_nickname ||
    formData.deposit_nickname ||
    formData.company_name ||
    formData.scheme_name ||
    formData.item_name ||
    formData.property_name ||
    formData.token_name ||
    type.name;

  // Filter out internal keys like portfolio_id
  const displayFields = Object.entries(formData).filter(([key, val]) => {
    if (key === 'portfolio_id') return false;
    if (val === undefined || val === null || val === '') return false;
    return true;
  });

  const formatKey = (key: string): string => {
    return key
      .replace(/_/g, ' ')
      .replace(/pct/i, '(%)')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const formatValue = (key: string, val: any): string => {
    if (typeof val === 'boolean') {
      return val ? 'Yes' : 'No';
    }
    if (typeof val === 'number') {
      if (key.includes('pct') || key.includes('rate') || key.includes('yield')) {
        return `${val}%`;
      }
      if (
        key.includes('balance') ||
        key.includes('amount') ||
        key.includes('price') ||
        key.includes('cost') ||
        key.includes('value') ||
        key.includes('fees') ||
        key.includes('taxes') ||
        key.includes('income') ||
        key.includes('threshold')
      ) {
        return `₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      }
      return val.toString();
    }
    return String(val);
  };

  return (
    <div className={styles.container}>
      <div className={styles.headerCard}>
        <div className={styles.headerInfo}>
          <span className={styles.categoryBadge}>
            {category.name} &bull; {type.name}
          </span>
          <h2 className={styles.investmentTitle}>{primaryName}</h2>
          <span className={styles.portfolioTag}>
            Recording in portfolio: <strong>{portfolio.name}</strong> ({portfolio.base_currency})
          </span>
        </div>
      </div>

      <div className={styles.bannerNotice}>
        Please review the entered investment attributes and contractual details. In Sprint 1, this flow validates your inputs, computes live client previews, and models the target investment record.
      </div>

      <div className={styles.detailsGrid}>
        {displayFields.map(([key, val]) => (
          <div key={key} className={styles.dataCard}>
            <span className={styles.dataLabel}>{formatKey(key)}</span>
            <span className={styles.dataValue}>{formatValue(key, val)}</span>
          </div>
        ))}
      </div>

      <FormActions
        onBack={onEdit}
        backLabel="Edit Details"
        submitLabel="Confirm & Add Investment"
        isSubmitting={isSubmitting}
        onSubmit={onConfirm}
      />
    </div>
  );
};
