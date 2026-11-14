import React from 'react';

export interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
}

export type NavigationItem = NavItem;

export interface SidebarProps {
  navItems: NavItem[];
  settingsItems?: NavItem[];
  user?: {
    full_name?: string;
    email?: string;
  } | null;
  dbStatus?: {
    label: string;
    color: string;
    dot: string;
  };
  onLogout?: () => void;
  isLoggingOut?: boolean;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  className?: string;
}

