import { forwardRef } from 'react';
import { InputProps } from './Input.types';
import styles from './Input.module.css';

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      size = 'md',
      error,
      helperText,
      leftIcon,
      rightIcon,
      disabled,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const isError = Boolean(error);
    const errorMessage = typeof error === 'string' ? error : undefined;

    const sizeClass = {
      sm: styles.sizeSm,
      md: styles.sizeMd,
      lg: styles.sizeLg,
    }[size];

    const inputClasses = [
      styles.input,
      sizeClass,
      leftIcon ? styles.hasLeftIcon : '',
      rightIcon ? styles.hasRightIcon : '',
      isError ? styles.hasError : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className={styles.container}>
        <div className={styles.inputWrapper}>
          {leftIcon && <span className={styles.leftIcon} aria-hidden="true">{leftIcon}</span>}
          <input
            ref={ref}
            id={id}
            disabled={disabled}
            aria-invalid={isError}
            className={inputClasses}
            {...props}
          />
          {rightIcon && <span className={styles.rightIcon}>{rightIcon}</span>}
        </div>
        {errorMessage && (
          <span className={styles.errorText} role="alert">
            {errorMessage}
          </span>
        )}
        {!errorMessage && helperText && (
          <span className={styles.helperText}>{helperText}</span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
