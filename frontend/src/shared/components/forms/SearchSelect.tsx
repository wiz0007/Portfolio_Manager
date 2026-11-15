import React, { useState, useRef, useEffect, useMemo, KeyboardEvent } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { FormField } from './FormField';
import styles from './SearchSelect.module.css';

export interface SearchSelectOption {
  value: string;
  label: string;
  subtitle?: string;
  group?: string;
}

export interface SearchSelectProps {
  id?: string;
  name?: string;
  value?: string | null;
  onChange?: (val: string) => void;
  onBlur?: () => void;
  options: SearchSelectOption[];
  placeholder?: string;
  searchPlaceholder?: string;
  allowCustom?: boolean;
  disabled?: boolean;
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

export const SearchSelect: React.FC<SearchSelectProps> = ({
  id,
  name,
  value,
  onChange,
  onBlur,
  options,
  placeholder = 'Select an option...',
  searchPlaceholder = 'Search...',
  allowCustom = false,
  disabled = false,
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
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleOutsideClick = (e: MouseEvent | TouchEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        onBlur?.();
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('touchstart', handleOutsideClick);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('touchstart', handleOutsideClick);
    };
  }, [isOpen, onBlur]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    } else {
      setSearchTerm('');
      setHighlightedIndex(0);
    }
  }, [isOpen]);

  const filteredOptions = useMemo(() => {
    if (!searchTerm.trim()) return options;
    const term = searchTerm.toLowerCase();
    const matches = options.filter(
      (opt) =>
        opt.label.toLowerCase().includes(term) ||
        opt.value.toLowerCase().includes(term) ||
        (opt.subtitle && opt.subtitle.toLowerCase().includes(term))
    );

    if (allowCustom && matches.length === 0 && searchTerm.trim()) {
      return [{ value: searchTerm.trim(), label: `Add "${searchTerm.trim()}"` }];
    }

    return matches;
  }, [options, searchTerm, allowCustom]);

  const selectedOption = useMemo(() => {
    return options.find((opt) => opt.value === value) || (value ? { value, label: value } : null);
  }, [options, value]);

  const handleSelect = (val: string) => {
    onChange?.(val);
    setIsOpen(false);
    onBlur?.();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev < filteredOptions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : filteredOptions.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredOptions[highlightedIndex]) {
        handleSelect(filteredOptions[highlightedIndex].value);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    }
  };

  const inputNode = (
    <div
      ref={containerRef}
      className={`${styles.selectContainer} ${isOpen ? styles.selectContainerOpen : ''} ${hasError ? styles.invalid : ''} ${className}`.trim()}
    >
      <button
        id={id}
        name={name}
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-invalid={hasError}
        aria-describedby={ariaDescribedBy}
        className={`${styles.triggerButton} ${hasError ? styles.invalid : ''}`}
      >
        <span className={selectedOption ? styles.selectedText : styles.placeholderText}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ''}`} />
      </button>

      {isOpen && (
        <div className={styles.dropdownMenu}>
          <div className={styles.searchInputWrapper}>
            <input
              ref={searchInputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={searchPlaceholder}
              className={styles.searchInput}
            />
          </div>

          <div className={styles.optionsList} role="listbox">
            {filteredOptions.length === 0 ? (
              <div className={styles.emptyState}>No options found</div>
            ) : (
              filteredOptions.map((opt, idx) => {
                const isSelected = opt.value === value;
                const isHighlighted = idx === highlightedIndex;

                return (
                  <div
                    key={opt.value}
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => handleSelect(opt.value)}
                    className={`${styles.optionItem} ${isSelected ? styles.optionSelected : ''} ${
                      isHighlighted ? styles.optionHighlighted : ''
                    }`}
                  >
                    <div>
                      <div>{opt.label}</div>
                      {opt.subtitle && <div className={styles.optionSubtitle}>{opt.subtitle}</div>}
                    </div>
                    {isSelected && <Check className="h-4 w-4 shrink-0 text-theme-primary" />}
                  </div>
                );
              })
            )}
          </div>
        </div>
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
