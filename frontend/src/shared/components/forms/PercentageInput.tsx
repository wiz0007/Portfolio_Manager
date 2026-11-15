import React, { ChangeEvent } from 'react';
import { FormField } from './FormField';
import styles from './PercentageInput.module.css';

export interface PercentageInputProps {
  id?: string;
  name?: string;
  value?: number | string | null;
  onChange?: (val: number | undefined) => void;
  onBlur?: () => void;
  min?: number;
  max?: number;
  step?: number | string;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
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

export const PercentageInput: React.FC<PercentageInputProps> = ({
  id,
  name,
  value,
  onChange,
  onBlur,
  min = 0,
  max = 100,
  step = '0.01',
  placeholder = '0.00',
  disabled = false,
  readOnly = false,
  isInvalid = false,
  className = '',
  'aria-describedby': ariaDescribedBy,
  label,
  required = false,
  optional = false,
  error,
  helperText,
}) => {
  const hasError = isInvalid || Boolean(error);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.trim();
    if (raw === '') {
      onChange?.(undefined);
      return;
    }

    if (/^\d*\.?\d*$/.test(raw)) {
      const parsed = parseFloat(raw);
      if (!isNaN(parsed)) {
        onChange?.(parsed);
      }
    }
  };

  const handleBlur = () => {
    if (value !== undefined && value !== null && value !== '') {
      let num = typeof value === 'number' ? value : parseFloat(value.toString());
      if (!isNaN(num)) {
        if (min !== undefined && num < min) num = min;
        if (max !== undefined && num > max) num = max;
        onChange?.(num);
      }
    }
    onBlur?.();
  };

  const inputNode = (
    <div className={`${styles.container} ${hasError ? styles.invalid : ''} ${className}`.trim()}>
      <input
        id={id}
        name={name}
        type="number"
        value={value ?? ''}
        onChange={handleChange}
        onBlur={handleBlur}
        min={min}
        max={max}
        step={step}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        aria-invalid={hasError}
        aria-describedby={ariaDescribedBy}
        className={`${styles.inputField} ${hasError ? styles.invalid : ''}`}
      />
      <span className={styles.percentSuffix} aria-hidden="true">
        %
      </span>
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
