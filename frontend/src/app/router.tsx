import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

export const AppRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <div className="flex min-h-screen items-center justify-center">
            <h1 className="text-2xl font-bold">Portfolio Manager Dashboard (Ready for Sprint 1)</h1>
          </div>
        }
      />
      <Route
        path="/login"
        element={
          <div className="flex min-h-screen items-center justify-center">
            <h1 className="text-2xl font-bold">Login</h1>
          </div>
        }
      />
      <Route
        path="/register"
        element={
          <div className="flex min-h-screen items-center justify-center">
            <h1 className="text-2xl font-bold">Register</h1>
          </div>
        }
      />
    </Routes>
  );
};
