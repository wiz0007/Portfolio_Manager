import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useCurrentUser } from '@/features/authentication/hooks/useAuth';
import { TrendingUp } from 'lucide-react';

export const ProtectedRoute: React.FC = () => {
  const { data: user, isLoading } = useCurrentUser();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-900 text-white">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 shadow-xl shadow-indigo-600/30 animate-pulse mb-4">
          <TrendingUp className="h-7 w-7 text-white" />
        </div>
        <p className="text-sm font-medium text-slate-400">Verifying authentication...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};

