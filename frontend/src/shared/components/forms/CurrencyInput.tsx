import React, { useState, useEffect, ChangeEvent } from 'react';
import { FormField } from './FormField';
import styles from './CurrencyInput.module.css';

export interface CurrencyInputProps {
  id?: string;
  name?: string;
  value?: number | string | null;
  onChange?: (val: number | undefined) => void;
  onBlur?: () => void;
  currency?: string;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  min?: number;
  max?: number;
  allowNegative?: boolean;
  isInvalid?: boolean;
  className?: string;
  'aria-describedby'?: string;
  // Accessible FormField wrapper props
  label?: string;
  required?: boolean;
  optional?: boolean;
  error?: string;
  helperText?: string;
}

const getCurrencySymbol = (code: string): string => {
  switch (code.toUpperCase()) {
    case 'INR':
      return '₹';
    case 'USD':
      return '$';
    case 'EUR':
      return '€';
    case 'GBP':
      return '£';
    case 'JPY':
      return '¥';
    default:
      return code;
  }
};

const formatWithCommas = (val: string | number, currency: string): string => {
  if (val === '' || val === null || val === undefined) return '';
  const num = typeof val === 'number' ? val : parseFloat(val.replace(/,/g, ''));
  if (isNaN(num)) return '';

  const parts = val.toString().replace(/,/g, '').split('.');
  const intPart = parts[0];
  const decPart = parts.length > 1 ? `.${parts[1].slice(0, 4)}` : '';

  if (currency.toUpperCase() === 'INR') {
    // Indian formatting (last 3, then groups of 2)
    const isNeg = intPart.startsWith('-');
    const cleanInt = isNeg ? intPart.slice(1) : intPart;
    if (cleanInt.length <= 3) {
      return (isNeg ? '-' : '') + cleanInt + decPart;
    }
    const lastThree = cleanInt.slice(-3);
    const otherNumbers = cleanInt.slice(0, -3);
    const formattedOthers = otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
    return (isNeg ? '-' : '') + formattedOthers + ',' + lastThree + decPart;
  }

  // Standard international formatting
  return num.toLocaleString('en-US', { maximumFractionDigits: 4 });
};

export const CurrencyInput: React.FC<CurrencyInputProps> = ({
  id,
  name,
  value,
  onChange,
  onBlur,
  currency = 'INR',
  placeholder = '0.00',
  disabled = false,
  readOnly = false,
  min,
  max,
  allowNegative = false,
  isInvalid = false,
  className = '',
  'aria-describedby': ariaDescribedBy,
  label,
  required = false,
  optional = false,
  error,
  helperText,
}) => {
  const [displayValue, setDisplayValue] = useState<string>('');
  const [isFocused, setIsFocused] = useState<boolean>(false);

  useEffect(() => {
    if (value === undefined || value === null || value === '') {
      setDisplayValue('');
    } else if (!isFocused) {
      setDisplayValue(formatWithCommas(value, currency));
    }
  }, [value, isFocused, currency]);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    let raw = e.target.value.replace(/,/g, '').trim();

    if (!allowNegative && raw.includes('-')) {
      raw = raw.replace(/-/g, '');
    }

    // Allow empty
    if (raw === '') {
      setDisplayValue('');
      onChange?.(undefined);
      return;
    }

    // Allow valid decimal typing like "12."
    if (/^-?\d*\.?\d*$/.test(raw)) {
      setDisplayValue(raw);
      const parsed = parseFloat(raw);
      if (!isNaN(parsed)) {
        onChange?.(parsed);
      }
    }
  };

  const handleFocus = () => {
    setIsFocused(true);
    if (value !== undefined && value !== null && value !== '') {
      setDisplayValue(value.toString());
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
    if (displayValue !== '') {
      let parsed = parseFloat(displayValue.replace(/,/g, ''));
      if (!isNaN(parsed)) {
        if (min !== undefined && parsed < min) parsed = min;
        if (max !== undefined && parsed > max) parsed = max;
        setDisplayValue(formatWithCommas(parsed, currency));
        onChange?.(parsed);
      } else {
        setDisplayValue('');
        onChange?.(undefined);
      }
    }
    onBlur?.();
  };

  const symbol = getCurrencySymbol(currency);
  const hasError = isInvalid || Boolean(error);

  const inputNode = (
    <div className={`${styles.inputContainer} ${hasError ? styles.invalid : ''} ${className}`.trim()}>
      <span className={styles.prefixSymbol} aria-hidden="true">
        {symbol}
      </span>
      <input
        id={id}
        name={name}
        type="text"
        inputMode="decimal"
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        disabled={disabled}
        readOnly={readOnly}
        placeholder={placeholder}
        aria-invalid={hasError}
        aria-describedby={ariaDescribedBy}
        className={`${styles.currencyField} ${hasError ? styles.invalid : ''}`}
      />
      {currency.length > 1 && (
        <span className={styles.suffixCode} aria-hidden="true">
          {currency}
        </span>
      )}
    </div>
  );

  if (label) {
    return (
      <FormField
        id={id}
        label={label}
        required={required}
        optional={optional}
        error={error}
        helperText={helperText}
      >
        {inputNode}
      </FormField>
    );
  }

  return inputNode;
};
