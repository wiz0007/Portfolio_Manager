import { forwardRef } from 'react';
import { LoadingStateProps } from './LoadingState.types';
import styles from './LoadingState.module.css';

export const LoadingState = forwardRef<HTMLDivElement, LoadingStateProps>(
  ({ message = 'Loading...', size = 'md', className = '', ...props }, ref) => {
    const sizeClass = {
      sm: styles.sizeSm,
      md: styles.sizeMd,
      lg: styles.sizeLg,
    }[size];

    return (
      <div
        ref={ref}
        role="status"
        aria-live="polite"
        className={`${styles.container} ${sizeClass} ${className}`.trim()}
        {...props}
      >
        <div className={styles.spinner} aria-hidden="true" />
        {message && <span className={styles.message}>{message}</span>}
      </div>
    );
  }
);

LoadingState.displayName = 'LoadingState';
