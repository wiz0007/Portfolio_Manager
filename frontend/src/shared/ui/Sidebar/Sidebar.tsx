import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { TrendingUp, Database, LogOut, X } from 'lucide-react';
import { Button } from '@/shared/ui/Button';
import styles from './Sidebar.module.css';
import { SidebarProps } from './Sidebar.types';

export const Sidebar: React.FC<SidebarProps> = ({
  navItems,
  settingsItems = [],
  user,
  dbStatus,
  onLogout,
  isLoggingOut = false,
  mobileOpen = false,
  onMobileClose,
  className = '',
}) => {
  // Close drawer on Escape key press
  useEffect(() => {
    if (!mobileOpen || !onMobileClose) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onMobileClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileOpen, onMobileClose]);

  const renderNavLinks = (onItemClick?: () => void) => (
    <div className={styles.navContent}>
      {/* Primary Navigation Section */}
      <div className={styles.navSection}>
        <div className={styles.sectionHeader}>Main Menu</div>
        <nav className={styles.navList} aria-label="Main Menu">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onItemClick}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ''}`
                }
              >
                <Icon className={styles.navIcon} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Settings Section */}
      {settingsItems.length > 0 && (
        <div className={styles.navSection}>
          <div className={styles.sectionHeader}>Settings</div>
          <nav className={styles.navList} aria-label="Settings Menu">
            {settingsItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onItemClick}
                  className={({ isActive }) =>
                    `${styles.navItem} ${isActive ? styles.active : ''}`
                  }
                >
                  <Icon className={styles.navIcon} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>
      )}
    </div>
  );

  const renderFooter = () => (
    <div className={styles.footer}>
      {dbStatus && (
        <div className={styles.statusPill}>
          <span
            className={`${styles.statusDot} ${dbStatus.dot}`}
            aria-hidden="true"
          />
          <Database className={`h-3.5 w-3.5 ${dbStatus.color}`} />
          <span className="truncate">{dbStatus.label}</span>
        </div>
      )}

      <div className={styles.userRow}>
        <div className={styles.userInfo}>
          <div className={styles.userName}>{user?.full_name || 'User'}</div>
          <div className={styles.userEmail}>{user?.email}</div>
        </div>

        {onLogout && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            disabled={isLoggingOut}
            title="Log out"
            aria-label="Log out"
            className="p-1.5 h-8 w-8 text-theme-text-muted hover:text-theme-negative"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* 1. Desktop Fixed Sidebar */}
      <aside
        className={`${styles.sidebar} ${styles.sidebarDesktop} ${className}`}
        aria-label="Application Sidebar"
      >
        <div className={styles.brand}>
          <div className={styles.brandIcon}>
            <TrendingUp className="h-5 w-5" />
          </div>
          <div className={styles.brandText}>
            <span className={styles.brandTitle}>Portfolio Manager</span>
            <span className={styles.brandSubtitle}>Financial Intelligence</span>
          </div>
        </div>

        {renderNavLinks()}
        {renderFooter()}
      </aside>

      {/* 2. Mobile Drawer & Overlay */}
      {mobileOpen && (
        <div
          className={styles.overlay}
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`${styles.drawer} ${mobileOpen ? styles.drawerOpen : ''}`}
        aria-label="Mobile Navigation"
        aria-hidden={!mobileOpen}
      >
        <div className={styles.brand} style={{ justifyContent: 'space-between' }}>
          <div className="flex items-center gap-3">
            <div className={styles.brandIcon}>
              <TrendingUp className="h-5 w-5" />
            </div>
            <span className={styles.brandTitle}>Portfolio Manager</span>
          </div>
          <button
            type="button"
            onClick={onMobileClose}
            className={styles.closeButton}
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {renderNavLinks(onMobileClose)}
        {renderFooter()}
      </aside>
    </>
  );
};

