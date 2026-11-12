import React from 'react';

export type ContainerMaxWidth = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  maxWidth?: ContainerMaxWidth;
}

