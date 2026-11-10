import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useCurrentUser, useLogout } from '@/features/authentication/hooks/useAuth';
import {
  TrendingUp,
  LogOut,
  User,
  ShieldCheck,
  Server,
  Database,
  Calendar,
  Layers,
} from 'lucide-react';
import { Button } from '@/shared/ui/Button';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';

export const DashboardPage: React.FC = () => {
  const { data: user } = useCurrentUser();
  const { mutate: logout, isPending: isLoggingOut } = useLogout();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout(undefined, {
      onSuccess: () => {
        navigate('/login', { replace: true });
      },
    });
  };

  const formattedDate = user?.date_joined
    ? new Date(user.date_joined).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Recent';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md">
              <TrendingUp className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              Portfolio Manager
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-800 bg-slate-800/60 px-3 py-1.5 text-xs text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Session Authenticated</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden md:block text-right">
                <div className="text-xs font-semibold text-white">{user?.full_name}</div>
                <div className="text-[11px] text-slate-400">{user?.email}</div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                isLoading={isLoggingOut}
                className="border-slate-700 bg-slate-800/60 text-slate-200 hover:bg-slate-700 hover:text-white"
              >
                <LogOut className="mr-1.5 h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {/* Welcome Banner */}
        <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 p-8 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-900/60 border border-indigo-700/50 px-2.5 py-0.5 text-xs font-medium text-indigo-300">
                <ShieldCheck className="h-3.5 w-3.5" /> Sprint 1 Foundation Active
              </span>
              <h1 className="text-3xl font-extrabold tracking-tight text-white">
                Welcome back, {user?.full_name || 'Investor'}!
              </h1>
              <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
                Your authenticated session is active and verified by Django REST Framework with
                HTTP-only cookies and CSRF protection.
              </p>
            </div>

            <div className="flex flex-wrap gap-4">
              <Link to="/settings/profile">
                <Button
                  variant="outline"
                  className="border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
                >
                  <User className="mr-2 h-4 w-4" /> View Profile
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Foundation & Architecture Cards */}
        <div>
          <h2 className="text-lg font-bold text-white mb-4">Architecture & Service Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Card className="border-slate-800 bg-slate-900 text-slate-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800/40">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base text-white">Authentication</CardTitle>
                  <CardDescription className="text-xs text-slate-400">
                    Cookie & Session Engine
                  </CardDescription>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Session identifiers regenerated on login, rate limited endpoints, and strict CSRF token validation on mutation APIs.
              </p>
            </Card>

            <Card className="border-slate-800 bg-slate-900 text-slate-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-lg bg-blue-950 text-blue-400 border border-blue-800/40">
                  <Server className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base text-white">Backend Monolith</CardTitle>
                  <CardDescription className="text-xs text-slate-400">
                    Django 5.1 + REST Framework
                  </CardDescription>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Modular domain apps architecture configured under <code className="text-indigo-300">/api/v1/</code> with OpenAPI contracts.
              </p>
            </Card>

            <Card className="border-slate-800 bg-slate-900 text-slate-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-lg bg-purple-950 text-purple-400 border border-purple-800/40">
                  <Database className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base text-white">Database Store</CardTitle>
                  <CardDescription className="text-xs text-slate-400">
                    PostgreSQL Compatible
                  </CardDescription>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Custom User model with UUID primary keys, normalized email uniqueness, and automated migrations.
              </p>
            </Card>
          </div>
        </div>

        {/* Current Account Details Card */}
        <Card className="border-slate-800 bg-slate-900 text-slate-100">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <User className="h-4 w-4 text-indigo-400" /> Account Profile Details
            </CardTitle>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" /> Member since {formattedDate}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-slate-400 uppercase tracking-wider text-[10px] mb-1">Account ID</div>
              <div className="font-mono text-slate-200 truncate">{user?.id}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-slate-400 uppercase tracking-wider text-[10px] mb-1">Full Name</div>
              <div className="font-semibold text-slate-200">{user?.full_name}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-slate-400 uppercase tracking-wider text-[10px] mb-1">Email Address</div>
              <div className="font-semibold text-slate-200">{user?.email}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-slate-400 uppercase tracking-wider text-[10px] mb-1">Next Sprint</div>
              <div className="font-semibold text-indigo-400 flex items-center gap-1">
                <Layers className="h-3.5 w-3.5" /> Sprint 2: App Shell & Dashboard
              </div>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
};

