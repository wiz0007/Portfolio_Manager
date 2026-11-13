import { forwardRef } from 'react';
import { BadgeProps } from './Badge.types';
import styles from './Badge.module.css';

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      children,
      variant = 'neutral',
      size = 'md',
      dot = false,
      className = '',
      ...props
    },
    ref
  ) => {
    const variantClass = {
      neutral: styles.variantNeutral,
      positive: styles.variantPositive,
      negative: styles.variantNegative,
      warning: styles.variantWarning,
      info: styles.variantInfo,
      brand: styles.variantBrand,
    }[variant];

    const sizeClass = {
      sm: styles.sizeSm,
      md: styles.sizeMd,
    }[size];

    const classNames = [
      styles.badge,
      variantClass,
      sizeClass,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <span ref={ref} className={classNames} {...props}>
        {dot && <span className={styles.dot} aria-hidden="true" />}
        <span>{children}</span>
      </span>
    );
  }
);

Badge.displayName = 'Badge';
