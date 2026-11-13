import React from 'react';

export type TrendDirection = 'up' | 'down' | 'neutral';

export interface MetricDisplayProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  delta?: string | number;
  trend?: TrendDirection;
  subtext?: string;
  icon?: React.ReactNode;
}

