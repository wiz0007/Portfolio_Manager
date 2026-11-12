import { forwardRef } from 'react';
import { PageHeaderProps } from './PageHeader.types';
import styles from './PageHeader.module.css';

export const PageHeader = forwardRef<HTMLDivElement, PageHeaderProps>(
  (
    {
      title,
      description,
      actions,
      breadcrumb,
      badge,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <header ref={ref} className={`${styles.container} ${className}`.trim()} {...props}>
        {breadcrumb && <div className={styles.breadcrumbWrapper}>{breadcrumb}</div>}
        <div className={styles.mainRow}>
          <div className={styles.titleArea}>
            <div className={styles.titleRow}>
              <h1 className={styles.title}>{title}</h1>
              {badge && <span>{badge}</span>}
            </div>
            {description && <p className={styles.description}>{description}</p>}
          </div>
          {actions && <div className={styles.actions}>{actions}</div>}
        </div>
      </header>
    );
  }
);

PageHeader.displayName = 'PageHeader';
