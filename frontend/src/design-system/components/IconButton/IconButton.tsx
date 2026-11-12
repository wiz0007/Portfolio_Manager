import { forwardRef } from 'react';
import { IconButtonProps } from './IconButton.types';
import styles from './IconButton.module.css';

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon,
      'aria-label': ariaLabel,
      variant = 'ghost',
      size = 'md',
      isLoading = false,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    const variantClass = {
      primary: styles.variantPrimary,
      secondary: styles.variantSecondary,
      outline: styles.variantOutline,
      ghost: styles.variantGhost,
      danger: styles.variantDanger,
    }[variant];

    const sizeClass = {
      sm: styles.sizeSm,
      md: styles.sizeMd,
      lg: styles.sizeLg,
    }[size];

    const classNames = [
      styles.iconButton,
      variantClass,
      sizeClass,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        aria-label={ariaLabel}
        title={ariaLabel}
        disabled={disabled || isLoading}
        className={classNames}
        {...props}
      >
        {isLoading ? <span className={styles.spinner} aria-hidden="true" /> : icon}
      </button>
    );
  }
);

IconButton.displayName = 'IconButton';
