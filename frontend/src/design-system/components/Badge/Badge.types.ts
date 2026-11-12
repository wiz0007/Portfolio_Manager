import React from 'react';

export type BadgeVariant = 'neutral' | 'positive' | 'negative' | 'warning' | 'info' | 'brand';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
}

