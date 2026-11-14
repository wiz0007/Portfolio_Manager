import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  BarChart3,
  Eye,
  User,
  Settings,
  Menu,
} from 'lucide-react';
import { useCurrentUser, useLogout } from '@/features/authentication/hooks/useAuth';
import { useHealthCheck } from '@/shared/hooks/useHealth';
import { Sidebar } from '@/shared/ui/Sidebar';
import { ThemeSwitcher } from '@/design-system';
import styles from './AuthenticatedLayout.module.css';

export const AuthenticatedLayout: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { data: user } = useCurrentUser();
  const { mutate: logout, isPending: isLoggingOut } = useLogout();
  const { data: healthData, isError: isHealthError, isLoading: isHealthLoading } = useHealthCheck();
  const navigate = useNavigate();
  const location = useLocation();

  const getDbStatus = () => {
    if (isHealthLoading) {
      return { label: 'DB: Checking...', color: 'text-amber-400', dot: 'bg-amber-400' };
    }
    if (isHealthError || healthData?.database !== 'connected') {
      return { label: 'DB: Unavailable', color: 'text-rose-400', dot: 'bg-rose-400' };
    }
    return { label: 'DB: Connected', color: 'text-emerald-400', dot: 'bg-emerald-400' };
  };

  const dbStatus = getDbStatus();

  const handleLogout = () => {
    logout(undefined, {
      onSuccess: () => {
        navigate('/login', { replace: true });
      },
    });
  };

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Portfolios', path: '/portfolios', icon: Briefcase },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
    { label: 'Watchlist', path: '/watchlist', icon: Eye },
  ];

  const settingsItems = [
    { label: 'Profile', path: '/settings/profile', icon: User },
    { label: 'Account', path: '/settings/account', icon: Settings },
  ];

  const getPageTitle = () => {
    const currentPath = location.pathname;
    if (currentPath.startsWith('/dashboard')) return 'Dashboard Overview';
    if (currentPath.startsWith('/portfolios')) return 'Portfolios';
    if (currentPath.startsWith('/analytics')) return 'Analytics & Insights';
    if (currentPath.startsWith('/watchlist')) return 'Watchlist';
    if (currentPath.startsWith('/settings/profile')) return 'Profile Settings';
    if (currentPath.startsWith('/settings/account')) return 'Account Settings';
    return 'Portfolio Manager';
  };

  return (
    <div className={styles.layoutContainer}>
      {/* Shared Unified Sidebar (Desktop & Mobile Drawer) */}
      <Sidebar
        navItems={navItems}
        settingsItems={settingsItems}
        user={user}
        dbStatus={dbStatus}
        onLogout={handleLogout}
        isLoggingOut={isLoggingOut}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className={styles.mainWrapper}>
        {/* Top Utility Header (64px, Utility Only) */}
        <header className={styles.topBar} role="banner">
          <div className={styles.topBarLeft}>
            <button
              type="button"
              className={styles.menuTrigger}
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open mobile menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h1 className={styles.pageTitle}>{getPageTitle()}</h1>
          </div>

          <div className={styles.topBarRight}>
            <ThemeSwitcher />
          </div>
        </header>

        {/* Dynamic Page Outlet */}
        <main className={styles.contentOutlet} role="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
