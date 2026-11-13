import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '@/shared/ui/Navbar';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-theme-bg text-theme-text transition-colors duration-200">
      <Navbar />
      <main className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
};

