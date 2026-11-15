import React from 'react';
import { Button } from '@/shared/ui/Button';
import styles from './FormActions.module.css';

export interface FormActionsProps {
  onBack?: () => void;
  onCancel?: () => void;
  backLabel?: string;
  submitLabel?: string;
  isSubmitting?: boolean;
  submitDisabled?: boolean;
  className?: string;
  onSubmit?: () => void;
}

export const FormActions: React.FC<FormActionsProps> = ({
  onBack,
  onCancel,
  backLabel = 'Back',
  submitLabel = 'Continue to Review',
  isSubmitting = false,
  submitDisabled = false,
  className = '',
  onSubmit,
}) => {
  return (
    <div className={`${styles.actionsContainer} ${className}`.trim()}>
      <div className={styles.leftGroup}>
        {onBack && (
          <Button type="button" variant="ghost" size="sm" onClick={onBack}>
            &larr; {backLabel}
          </Button>
        )}
        {onCancel && (
          <Button type="button" variant="outline" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>

      <div className={styles.rightGroup}>
        <Button
          type={onSubmit ? 'button' : 'submit'}
          onClick={onSubmit}
          size="sm"
          disabled={submitDisabled || isSubmitting}
          className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm"
        >
          {isSubmitting ? 'Processing...' : submitLabel}
        </Button>
      </div>
    </div>
  );
};
