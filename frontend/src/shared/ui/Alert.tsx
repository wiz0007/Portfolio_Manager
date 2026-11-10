import * as React from 'react';
import { cn } from '../lib/utils';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'error' | 'success' | 'info';
  title?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'error',
  title,
  children,
  className,
  ...props
}) => {
  const icons = {
    error: <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />,
    success: <CheckCircle className="h-5 w-5 text-emerald-600 flex-shrink-0" />,
    info: <Info className="h-5 w-5 text-blue-600 flex-shrink-0" />,
  };

  const variants = {
    error: 'border-red-200 bg-red-50 text-red-900',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    info: 'border-blue-200 bg-blue-50 text-blue-900',
  };

  return (
    <div
      role="alert"
      className={cn('flex items-start gap-3 rounded-lg border p-4 text-sm', variants[variant], className)}
      {...props}
    >
      {icons[variant]}
      <div className="space-y-1">
        {title && <h5 className="font-semibold">{title}</h5>}
        <div className="text-xs leading-relaxed">{children}</div>
      </div>
    </div>
  );
};

