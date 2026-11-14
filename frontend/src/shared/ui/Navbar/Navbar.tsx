import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import { ThemeToggle } from '@/design-system';
import styles from './Navbar.module.css';

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
    <div className={styles.brandContainer}>
      <div className={styles.brandIcon}>
        <TrendingUp className="h-5 w-5" />
      </div>
      <span className={styles.brandTitle}>Portfolio Manager</span>
    </div>
  );

  return (
    <header className={`${styles.navbar} ${className}`.trim()} role="banner">
      <div>
        {showBrandLink ? (
          <Link
            to="/"
            className={styles.brandLink}
            aria-label="Portfolio Manager Home"
          >
            {brandElement}
          </Link>
        ) : (
          brandElement
        )}
      </div>

      <div className={styles.rightGroup}>
        {rightContent}
        <ThemeToggle />
      </div>
    </header>
  );
};

