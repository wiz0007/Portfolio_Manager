import React, { ReactNode } from 'react';
import styles from './FormSection.module.css';

export interface FormSectionProps {
  title: string;
  description?: string;
  columns?: 1 | 2 | 3;
  children: ReactNode;
  className?: string;
}

export const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  columns = 2,
  children,
  className = '',
}) => {
  const gridClass =
    columns === 3
      ? styles.contentGrid3Col
      : columns === 2
      ? styles.contentGrid2Col
      : styles.contentGrid;

  return (
    <section className={`${styles.section} ${className}`.trim()}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {description && <p className={styles.description}>{description}</p>}
      </div>
      <div className={`${styles.contentGrid} ${gridClass}`}>{children}</div>
    </section>
  );
};
