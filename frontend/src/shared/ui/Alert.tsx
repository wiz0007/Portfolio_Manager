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
    error: <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />,
    success: <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0" />,
    info: <Info className="h-5 w-5 text-cyan-400 shrink-0" />,
  };

  const variants = {
    error: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
    success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
    info: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300',
  };

  return (
    <div
      role="alert"
      className={cn('flex items-start gap-3 rounded-lg border p-4 text-sm', variants[variant], className)}
      {...props}
    >
      {icons[variant]}
      <div className="space-y-1">
        {title && <h5 className="font-semibold text-theme-text">{title}</h5>}
        <div className="text-xs leading-relaxed">{children}</div>
      </div>
    </div>
  );
};
