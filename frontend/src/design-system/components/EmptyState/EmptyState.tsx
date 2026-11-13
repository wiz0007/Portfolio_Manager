import { forwardRef } from 'react';
import { EmptyStateProps } from './EmptyState.types';
import styles from './EmptyState.module.css';

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ icon, title, description, action, className = '', ...props }, ref) => {
    return (
      <div ref={ref} className={`${styles.container} ${className}`.trim()} {...props}>
        {icon && (
          <div className={styles.iconWrapper} aria-hidden="true">
            {icon}
          </div>
        )}
        <h3 className={styles.title}>{title}</h3>
        {description && <p className={styles.description}>{description}</p>}
        {action && <div className={styles.actionWrapper}>{action}</div>}
      </div>
    );
  }
);

EmptyState.displayName = 'EmptyState';
