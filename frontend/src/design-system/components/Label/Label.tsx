import { forwardRef } from 'react';
import { LabelProps } from './Label.types';
import styles from './Label.module.css';

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ children, required, disabled, className = '', ...props }, ref) => {
    const classNames = [
      styles.label,
      disabled ? styles.disabled : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <label ref={ref} className={classNames} {...props}>
        {children}
        {required && <span className={styles.requiredIndicator} aria-hidden="true">*</span>}
      </label>
    );
  }
);

Label.displayName = 'Label';
