import React from 'react';

export type StatusVariant = 'positive' | 'negative' | 'warning' | 'info' | 'neutral';

export interface StatusIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: StatusVariant;
  label?: string;
  pulse?: boolean;
}

