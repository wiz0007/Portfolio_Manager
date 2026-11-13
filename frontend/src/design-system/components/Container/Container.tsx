import { forwardRef } from 'react';
import { ContainerProps } from './Container.types';
import styles from './Container.module.css';

export const Container = forwardRef<HTMLDivElement, ContainerProps>(
  ({ maxWidth = 'xl', className = '', children, ...props }, ref) => {
    const maxClass = {
      sm: styles.maxSm,
      md: styles.maxMd,
      lg: styles.maxLg,
      xl: styles.maxXl,
      full: styles.maxFull,
    }[maxWidth];

    return (
      <div ref={ref} className={`${styles.container} ${maxClass} ${className}`.trim()} {...props}>
        {children}
      </div>
    );
  }
);

Container.displayName = 'Container';
