import { forwardRef } from 'react';
import { GridProps } from './Grid.types';
import styles from './Grid.module.css';

export const Grid = forwardRef<HTMLDivElement, GridProps>(
  ({ cols = 1, gap = 'md', className = '', children, ...props }, ref) => {
    const colsClass = {
      1: styles.cols1,
      2: styles.cols2,
      3: styles.cols3,
      4: styles.cols4,
      5: styles.cols4, // fallback to 4
      6: styles.cols6,
      12: styles.cols12,
    }[cols];

    const gapClass = {
      none: styles.gapNone,
      xs: styles.gapXs,
      sm: styles.gapSm,
      md: styles.gapMd,
      lg: styles.gapLg,
      xl: styles.gapXl,
      '2xl': styles.gap2xl,
    }[gap];

    const classNames = [
      styles.grid,
      colsClass,
      gapClass,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div ref={ref} className={classNames} {...props}>
        {children}
      </div>
    );
  }
);

Grid.displayName = 'Grid';
