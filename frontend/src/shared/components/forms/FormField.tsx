import React, { ReactNode } from 'react';
import styles from './FormField.module.css';

export interface FormFieldProps {
  id?: string;
  htmlFor?: string;
  label: string;
  required?: boolean;
  optional?: boolean;
  error?: string;
  helperText?: string;
  children: ReactNode;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  id,
  htmlFor,
  label,
  required = false,
  optional = false,
  error,
  helperText,
  children,
  className = '',
}) => {
  const targetId = id || htmlFor;
  const errorId = targetId ? `${targetId}-error` : undefined;
  const helperId = targetId ? `${targetId}-helper` : undefined;

  return (
    <div className={`${styles.fieldWrapper} ${className}`.trim()}>
      <div className={styles.labelRow}>
        <label htmlFor={targetId} className={styles.label}>
          <span>{label}</span>
          {required && <span className={styles.requiredAsterisk} aria-hidden="true">*</span>}
          {optional && <span className={styles.optionalBadge}>(Optional)</span>}
        </label>
      </div>

      {children}

      {error ? (
        <span id={errorId} className={styles.errorMessage} role="alert">
          {error}
        </span>
      ) : helperText ? (
        <span id={helperId} className={styles.helperText}>
          {helperText}
        </span>
      ) : null}
    </div>
  );
};
