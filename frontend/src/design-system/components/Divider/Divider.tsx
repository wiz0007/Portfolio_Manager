import { forwardRef } from 'react';
import { DividerProps } from './Divider.types';
import styles from './Divider.module.css';

export const Divider = forwardRef<HTMLDivElement, DividerProps>(
  ({ orientation = 'horizontal', label, className = '', ...props }, ref) => {
    if (label && orientation === 'horizontal') {
      return (
        <div ref={ref} className={`${styles.withLabel} ${className}`.trim()} role="separator" {...props}>
          <div className={styles.line} />
          <span className={styles.label}>{label}</span>
          <div className={styles.line} />
        </div>
      );
    }

    const orientationClass = orientation === 'vertical' ? styles.vertical : styles.horizontal;
    return (
      <div
        ref={ref}
        role="separator"
        aria-orientation={orientation}
        className={`${orientationClass} ${className}`.trim()}
        {...props}
      />
    );
  }
);

Divider.displayName = 'Divider';
