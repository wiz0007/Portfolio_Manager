import { forwardRef } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { ErrorStateProps } from './ErrorState.types';
import { Button } from '../Button';
import styles from './ErrorState.module.css';

export const ErrorState = forwardRef<HTMLDivElement, ErrorStateProps>(
  (
    {
      title = 'Something went wrong',
      message = 'Failed to load data. Please check your connection and try again.',
      onRetry,
      retryLabel = 'Try Again',
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <div ref={ref} role="alert" className={`${styles.container} ${className}`.trim()} {...props}>
        <div className={styles.iconWrapper} aria-hidden="true">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h4 className={styles.title}>{title}</h4>
        {message && <p className={styles.message}>{message}</p>}
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
            {retryLabel}
          </Button>
        )}
      </div>
    );
  }
);

ErrorState.displayName = 'ErrorState';
