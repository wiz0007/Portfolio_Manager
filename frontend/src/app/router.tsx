import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/features/authentication/pages/LoginPage';
import { RegisterPage } from '@/features/authentication/pages/RegisterPage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { ProfilePage } from '@/features/settings/pages/ProfilePage';
import { AccountPage } from '@/features/settings/pages/AccountPage';
import { ProtectedRoute } from './layouts/ProtectedRoute';
import { PublicOnlyRoute } from './layouts/PublicOnlyRoute';

export const AppRouter: React.FC = () => {
  return (
    <Routes>
      {/* Public routes (redirect to /dashboard if already logged in) */}
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected routes (redirect to /login if unauthenticated) */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/settings/profile" element={<ProfilePage />} />
        <Route path="/settings/account" element={<AccountPage />} />
      </Route>

      {/* Fallback & Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
