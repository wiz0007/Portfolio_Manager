import { forwardRef } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { MetricDisplayProps } from './MetricDisplay.types';
import styles from './MetricDisplay.module.css';

export const MetricDisplay = forwardRef<HTMLDivElement, MetricDisplayProps>(
  (
    {
      label,
      value,
      delta,
      trend,
      subtext,
      icon,
      className = '',
      ...props
    },
    ref
  ) => {
    // If trend is not explicitly provided, infer from delta sign if delta is string/number
    let inferredTrend = trend;
    if (!inferredTrend && delta !== undefined) {
      const deltaStr = String(delta).trim();
      if (deltaStr.startsWith('+')) inferredTrend = 'up';
      else if (deltaStr.startsWith('-')) inferredTrend = 'down';
      else inferredTrend = 'neutral';
    }

    const trendClass = {
      up: styles.trendUp,
      down: styles.trendDown,
      neutral: styles.trendNeutral,
    }[inferredTrend || 'neutral'];

    const TrendIcon = {
      up: ArrowUpRight,
      down: ArrowDownRight,
      neutral: Minus,
    }[inferredTrend || 'neutral'];

    return (
      <div ref={ref} className={`${styles.container} ${className}`.trim()} {...props}>
        <div className={styles.header}>
          <span className={styles.label}>{label}</span>
          {icon && <span className={styles.icon} aria-hidden="true">{icon}</span>}
        </div>

        <div className={styles.valueRow}>
          <span className={styles.value}>{value}</span>
          {delta !== undefined && (
            <span className={`${styles.delta} ${trendClass}`}>
              <TrendIcon className="w-3 h-3 shrink-0" aria-hidden="true" />
              <span>{delta}</span>
            </span>
          )}
        </div>

        {subtext && <span className={styles.subtext}>{subtext}</span>}
      </div>
    );
  }
);

MetricDisplay.displayName = 'MetricDisplay';
