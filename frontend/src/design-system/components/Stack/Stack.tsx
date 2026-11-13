import { forwardRef } from 'react';
import { StackProps } from './Stack.types';
import styles from './Stack.module.css';

export const Stack = forwardRef<HTMLDivElement, StackProps>(
  (
    {
      direction = 'column',
      spacing = 'md',
      align,
      justify,
      wrap = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const directionClass = direction === 'row' ? styles.row : styles.column;

    const spacingClass = {
      none: styles.gapNone,
      xs: styles.gapXs,
      sm: styles.gapSm,
      md: styles.gapMd,
      lg: styles.gapLg,
      xl: styles.gapXl,
      '2xl': styles.gap2xl,
    }[spacing];

    const alignClass = align
      ? {
          start: styles.alignStart,
          center: styles.alignCenter,
          end: styles.alignEnd,
          stretch: styles.alignStretch,
          baseline: styles.alignBaseline,
        }[align]
      : '';

    const justifyClass = justify
      ? {
          start: styles.justifyStart,
          center: styles.justifyCenter,
          end: styles.justifyEnd,
          between: styles.justifyBetween,
          around: styles.justifyAround,
        }[justify]
      : '';

    const classNames = [
      styles.stack,
      directionClass,
      spacingClass,
      alignClass,
      justifyClass,
      wrap ? styles.wrap : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div ref={ref} className={classNames} {...props}>
        {children}
      </div>
    );
  }
);

Stack.displayName = 'Stack';
