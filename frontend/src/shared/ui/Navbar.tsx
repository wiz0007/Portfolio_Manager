import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import { ThemeToggle } from '@/design-system';

export interface NavbarProps {
  className?: string;
  showBrandLink?: boolean;
  rightContent?: React.ReactNode;
}

export const Navbar: React.FC<NavbarProps> = ({
  className = '',
  showBrandLink = true,
  rightContent,
}) => {
  const brandElement = (
    <div className="flex items-center gap-2.5 group">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-theme-primary text-theme-text-inverse shadow-sm transition-transform group-hover:scale-105">
        <TrendingUp className="h-5 w-5" />
      </div>
      <span className="text-base font-bold tracking-tight text-theme-text">
        Portfolio Manager
      </span>
    </div>
  );

  return (
    <header
      className={`h-16 border-b border-theme-border bg-theme-surface/85 backdrop-blur-md sticky top-0 z-30 px-4 sm:px-8 flex items-center justify-between transition-colors duration-200 ${className}`.trim()}
    >
      <div className="flex items-center">
        {showBrandLink ? (
          <Link
            to="/"
            className="focus:outline-none focus:ring-2 focus:ring-theme-primary rounded-lg transition-opacity hover:opacity-90"
            aria-label="Portfolio Manager Home"
          >
            {brandElement}
          </Link>
        ) : (
          brandElement
        )}
      </div>

      <div className="flex items-center gap-3">
        {rightContent}
        {/* Theme selection on top right */}
        <ThemeToggle />
      </div>
    </header>
  );
};

