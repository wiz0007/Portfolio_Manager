import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { DialogProps } from './Dialog.types';
import styles from './Dialog.module.css';

export const Dialog: React.FC<DialogProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth = 'md',
  className = '',
}) => {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxClass = {
    sm: styles.maxSm,
    md: styles.maxMd,
    lg: styles.maxLg,
  }[maxWidth];

  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'dialog-title' : undefined}
        aria-describedby={description ? 'dialog-desc' : undefined}
        className={`${styles.panel} ${maxClass} ${className}`.trim()}
      >
        <div className={styles.header}>
          <div className={styles.titleArea}>
            {title && (
              <h3 id="dialog-title" className={styles.title}>
                {title}
              </h3>
            )}
            {description && (
              <p id="dialog-desc" className={styles.description}>
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className={styles.closeButton}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className={styles.body}>{children}</div>

        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>
  );
};

