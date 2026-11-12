import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  BarChart3,
  Eye,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  TrendingUp,
  Database,
} from 'lucide-react';
import { useCurrentUser, useLogout } from '@/features/authentication/hooks/useAuth';
import { useHealthCheck } from '@/shared/hooks/useHealth';
import { Button } from '@/shared/ui/Button';
import { ThemeSwitcher } from '@/design-system';

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

  // Helper to determine active page title
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
    <div className="min-h-screen bg-theme-bg text-theme-text flex transition-colors duration-200">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r border-theme-border bg-theme-surface/90 backdrop-blur shrink-0 transition-colors duration-200">
        {/* Brand */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-theme-border">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-theme-primary text-theme-text-inverse shadow-md">
            <TrendingUp className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-theme-text">Portfolio Manager</div>
            <div className="text-[10px] text-theme-primary font-medium">Financial Intelligence</div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          <div>
            <div className="px-2 mb-2 text-[11px] font-semibold tracking-wider text-theme-text-muted uppercase">
              Main Menu
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-theme-primary-subtle text-theme-primary border border-theme-primary/30'
                          : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div>
            <div className="px-2 mb-2 text-[11px] font-semibold tracking-wider text-theme-text-muted uppercase">
              Settings
            </div>
            <nav className="space-y-1">
              {settingsItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-theme-primary-subtle text-theme-primary border border-theme-primary/30'
                          : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Database & User footer */}
        <div className="p-4 border-t border-theme-border space-y-3">
          <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-theme-card border border-theme-border text-[11px] text-theme-text-secondary">
            <span className={`h-2 w-2 rounded-full ${dbStatus.dot}`} />
            <Database className={`h-3.5 w-3.5 ${dbStatus.color}`} />
            <span className="truncate">{dbStatus.label}</span>
          </div>

          <div className="flex items-center justify-between pt-1">
            <div className="min-w-0 pr-2">
              <div className="text-xs font-medium text-theme-text truncate">
                {user?.full_name || 'User'}
              </div>
              <div className="text-[11px] text-theme-text-muted truncate">{user?.email}</div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              disabled={isLoggingOut}
              title="Log out"
              className="text-theme-text-muted hover:text-theme-negative p-1.5 h-8 w-8"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-theme-bg/80 backdrop-blur-sm md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-theme-surface border-r border-theme-border flex flex-col transform transition-transform duration-200 ease-in-out md:hidden ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-16 flex items-center justify-between px-6 border-b border-theme-border">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-theme-primary text-theme-text-inverse">
              <TrendingUp className="h-5 w-5" />
            </div>
            <span className="text-sm font-bold text-theme-text">Portfolio Manager</span>
          </div>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="text-theme-text-muted hover:text-theme-text p-1 rounded-md"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          <div>
            <div className="px-2 mb-2 text-[11px] font-semibold tracking-wider text-theme-text-muted uppercase">
              Main Menu
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                        isActive
                          ? 'bg-theme-primary-subtle text-theme-primary border border-theme-primary/30'
                          : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div>
            <div className="px-2 mb-2 text-[11px] font-semibold tracking-wider text-theme-text-muted uppercase">
              Settings
            </div>
            <nav className="space-y-1">
              {settingsItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                        isActive
                          ? 'bg-theme-primary-subtle text-theme-primary border border-theme-primary/30'
                          : 'text-theme-text-muted hover:text-theme-text hover:bg-theme-hover'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>

        <div className="p-4 border-t border-theme-border space-y-3">
          <div className="text-xs text-theme-text-secondary truncate">{user?.full_name}</div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="w-full text-theme-text-secondary border-theme-border hover:bg-theme-hover"
          >
            <LogOut className="mr-2 h-4 w-4" /> Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 bg-theme-bg">
        {/* Header */}
        <header className="h-16 border-b border-theme-border bg-theme-surface/80 backdrop-blur sticky top-0 z-30 px-4 sm:px-8 flex items-center justify-between transition-colors duration-200">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 text-theme-text-muted hover:text-theme-text rounded-lg hover:bg-theme-hover"
              aria-label="Open sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h2 className="text-lg font-semibold text-theme-text tracking-tight">
              {getPageTitle()}
            </h2>
          </div>

          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Theme Selector Component in Header Top-Right Area */}
            <ThemeSwitcher />

            <div className="hidden sm:flex items-center gap-2 rounded-full border border-theme-border bg-theme-card px-3 py-1 text-xs text-theme-text-secondary">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Session Authenticated</span>
            </div>

            <div className="flex items-center gap-2 pl-2 border-l border-theme-border">
              <NavLink
                to="/settings/profile"
                className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-theme-hover text-theme-text-secondary hover:text-theme-text transition-colors"
                title="Profile"
              >
                <div className="h-7 w-7 rounded-full bg-theme-primary/20 border border-theme-primary/40 flex items-center justify-center text-xs font-bold text-theme-primary">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
                <span className="hidden lg:inline text-xs font-medium text-theme-text">
                  {user?.full_name}
                </span>
              </NavLink>
            </div>
          </div>
        </header>

        {/* Email Verification Pending Banner */}
        {user && user.is_email_verified === false && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 sm:px-8 py-2.5 flex items-center justify-between text-xs text-amber-200">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse shrink-0" />
              <span>Your email is not verified yet. Check your inbox or request a new verification link.</span>
            </div>
            <NavLink
              to="/settings/account"
              className="text-xs font-semibold text-amber-300 hover:text-white underline underline-offset-2 ml-4 shrink-0"
            >
              Verify Email &rarr;
            </NavLink>
          </div>
        )}

        {/* Page Content Body */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
