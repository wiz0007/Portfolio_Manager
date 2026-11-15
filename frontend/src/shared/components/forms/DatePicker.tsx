import React, { ChangeEvent } from 'react';
import { FormField } from './FormField';
import styles from './DatePicker.module.css';

export interface DatePickerProps {
  id?: string;
  name?: string;
  value?: string | null; // Expected YYYY-MM-DD
  onChange?: (val: string) => void;
  onBlur?: () => void;
  min?: string;
  max?: string;
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

export const DatePicker: React.FC<DatePickerProps> = ({
  id,
  name,
  value,
  onChange,
  onBlur,
  min,
  max,
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
    onChange?.(e.target.value);
  };

  const inputNode = (
    <div className={`${styles.container} ${hasError ? styles.invalid : ''} ${className}`.trim()}>
      <input
        id={id}
        name={name}
        type="date"
        value={value ?? ''}
        onChange={handleChange}
        onBlur={onBlur}
        min={min}
        max={max}
        disabled={disabled}
        readOnly={readOnly}
        aria-invalid={hasError}
        aria-describedby={ariaDescribedBy}
        className={`${styles.dateField} ${hasError ? styles.invalid : ''}`}
      />
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
