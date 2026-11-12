import React from 'react';
import { StackSpacing } from '../Stack/Stack.types';

export type GridCols = 1 | 2 | 3 | 4 | 5 | 6 | 12;

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: GridCols;
  gap?: StackSpacing;
}

