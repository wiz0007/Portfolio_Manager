import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/features/authentication/pages/LoginPage';
import { RegisterPage } from '@/features/authentication/pages/RegisterPage';
import { ForgotPasswordPage } from '@/features/authentication/pages/ForgotPasswordPage';
import { VerifyEmailPage } from '@/features/authentication/pages/VerifyEmailPage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { PortfoliosPage } from '@/features/portfolios/pages/PortfoliosPage';
import { PortfolioCreatePage } from '@/features/portfolios/pages/PortfolioCreatePage';
import { PortfolioDetailPage } from '@/features/portfolios/pages/PortfolioDetailPage';
import { PortfolioEditPage } from '@/features/portfolios/pages/PortfolioEditPage';
import { ProfilePage } from '@/features/settings/pages/ProfilePage';
import { AccountPage } from '@/features/settings/pages/AccountPage';
import { AnalyticsPlaceholderPage } from '@/features/analytics/pages/AnalyticsPlaceholderPage';
import { WatchlistPlaceholderPage } from '@/features/watchlists/pages/WatchlistPlaceholderPage';
import { ProtectedRoute } from './layouts/ProtectedRoute';
import { PublicOnlyRoute } from './layouts/PublicOnlyRoute';
import { AuthenticatedLayout } from './layouts/AuthenticatedLayout';
import { AuthLayout } from './layouts/AuthLayout';

export const AppRouter: React.FC = () => {
  return (
    <Routes>
      {/* Public-only routes with Top Navbar */}
      <Route element={<PublicOnlyRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        </Route>
      </Route>

      {/* Universal routes with Top Navbar */}
      <Route element={<AuthLayout />}>
        <Route path="/verify-email" element={<VerifyEmailPage />} />
      </Route>

      {/* Protected routes (redirect to /login if unauthenticated) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AuthenticatedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/portfolios" element={<PortfoliosPage />} />
          <Route path="/portfolios/new" element={<PortfolioCreatePage />} />
          <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
          <Route path="/portfolios/:id/edit" element={<PortfolioEditPage />} />
          <Route path="/analytics" element={<AnalyticsPlaceholderPage />} />
          <Route path="/watchlist" element={<WatchlistPlaceholderPage />} />
          <Route path="/settings/profile" element={<ProfilePage />} />
          <Route path="/settings/account" element={<AccountPage />} />
        </Route>
      </Route>

      {/* Fallback & Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
