import React from 'react';

export type DialogMaxWidth = 'sm' | 'md' | 'lg';

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  description?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: DialogMaxWidth;
  className?: string;
}

