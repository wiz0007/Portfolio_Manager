import React from 'react';
import { Check } from 'lucide-react';
import { AssetCategoryConfig, AssetTypeConfig } from '../../types/investmentTypes';
import styles from './AssetTypeSelector.module.css';

export interface AssetTypeSelectorProps {
  category: AssetCategoryConfig;
  selectedTypeId?: string;
  onSelectType: (type: AssetTypeConfig) => void;
}

export const AssetTypeSelector: React.FC<AssetTypeSelectorProps> = ({
  category,
  selectedTypeId,
  onSelectType,
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Select Investment Product in {category.name}</h2>
        <p className={styles.description}>
          Choose the specific instrument variant to launch its custom data-entry workflow.
        </p>
      </div>

      <div className={styles.grid}>
        {category.types.map((type) => {
          const isSelected = selectedTypeId === type.id;

          return (
            <div
              key={type.id}
              role="button"
              tabIndex={0}
              className={`${styles.typeCard} ${isSelected ? styles.selectedCard : ''}`}
              onClick={() => onSelectType(type)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectType(type);
                }
              }}
            >
              <div className={styles.cardHeader}>
                <h3 className={styles.typeName}>{type.name}</h3>
                {isSelected && <Check size={18} color="var(--color-primary)" />}
              </div>

              <p className={styles.typeDescription}>{type.description}</p>

              <div className={styles.metaRow}>
                <span className={styles.metaBadge}>Valuation: {type.defaultValuationMethod}</span>
                {type.hasContractualMaturity && (
                  <span className={styles.metaBadge}>Contractual Maturity</span>
                )}
                {type.supportsFutureProjection && (
                  <span className={styles.metaBadge}>Yield Projection</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
