import { forwardRef } from 'react';
import { StatusIndicatorProps } from './StatusIndicator.types';
import styles from './StatusIndicator.module.css';

export const StatusIndicator = forwardRef<HTMLDivElement, StatusIndicatorProps>(
  (
    {
      variant = 'neutral',
      label,
      pulse = false,
      className = '',
      ...props
    },
    ref
  ) => {
    const variantClass = {
      positive: styles.variantPositive,
      negative: styles.variantNegative,
      warning: styles.variantWarning,
      info: styles.variantInfo,
      neutral: styles.variantNeutral,
    }[variant];

    return (
      <div ref={ref} className={`${styles.container} ${variantClass} ${className}`.trim()} {...props}>
        <span className={styles.dotWrapper} aria-hidden="true">
          {pulse && <span className={styles.pulse} />}
          <span className={styles.dot} />
        </span>
        {label && <span>{label}</span>}
      </div>
    );
  }
);

StatusIndicator.displayName = 'StatusIndicator';
