import React from 'react';
import {
  Landmark,
  ShieldCheck,
  TrendingUp,
  Layers,
  Gem,
  Home,
  Bitcoin,
  Check,
} from 'lucide-react';
import { ASSET_CATEGORIES } from '../../config/assetCategories';
import { AssetCategoryConfig, AssetCategory } from '../../types/investmentTypes';
import styles from './AssetCategorySelector.module.css';

const ICON_MAP: Record<string, React.ReactNode> = {
  Landmark: <Landmark size={20} />,
  ShieldCheck: <ShieldCheck size={20} />,
  TrendingUp: <TrendingUp size={20} />,
  Layers: <Layers size={20} />,
  Gem: <Gem size={20} />,
  Home: <Home size={20} />,
  Bitcoin: <Bitcoin size={20} />,
};

export interface AssetCategorySelectorProps {
  selectedCategoryId?: AssetCategory;
  onSelectCategory: (category: AssetCategoryConfig) => void;
}

export const AssetCategorySelector: React.FC<AssetCategorySelectorProps> = ({
  selectedCategoryId,
  onSelectCategory,
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Select Asset Category</h2>
        <p className={styles.description}>
          Choose the investment class. Each category provides dedicated domain attributes, valuation models, and contractual rules.
        </p>
      </div>

      <div className={styles.grid}>
        {ASSET_CATEGORIES.map((category) => {
          const isSelected = selectedCategoryId === category.id;
          const icon = ICON_MAP[category.iconName] || <Landmark size={20} />;

          return (
            <div
              key={category.id}
              role="button"
              tabIndex={0}
              className={`${styles.categoryCard} ${isSelected ? styles.selectedCard : ''}`}
              onClick={() => onSelectCategory(category)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectCategory(category);
                }
              }}
            >
              <div className={styles.cardHeader}>
                <div className={styles.iconBox}>{icon}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className={styles.typeCountBadge}>{category.types.length} Types</span>
                  {isSelected && <Check size={16} color="var(--color-primary)" />}
                </div>
              </div>

              <h3 className={styles.categoryName}>{category.name}</h3>
              <p className={styles.categoryDescription}>{category.description}</p>

              <div className={styles.typesList}>
                {category.types.map((type) => (
                  <span key={type.id} className={styles.typePill}>
                    {type.name}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
