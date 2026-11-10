import React from 'react';
import { Link } from 'react-router-dom';
import { useCurrentUser } from '@/features/authentication/hooks/useAuth';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { ArrowLeft, Key, Lock, AlertTriangle } from 'lucide-react';

export const AccountPage: React.FC = () => {
  const { data: user } = useCurrentUser();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link to="/dashboard">
          <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white mb-2">
            <ArrowLeft className="mr-1.5 h-4 w-4" /> Back to Dashboard
          </Button>
        </Link>

        <div>
          <h1 className="text-2xl font-bold text-white">Account Security</h1>
          <p className="text-sm text-slate-400">Security policies and session management</p>
        </div>

        <Card className="border-slate-800 bg-slate-900 text-slate-100">
          <CardTitle className="text-lg text-white mb-1">Security Overview</CardTitle>
          <CardDescription className="text-xs text-slate-400 mb-6">
            Account protection configured for {user?.email}
          </CardDescription>

          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start gap-4">
              <Key className="h-5 w-5 text-indigo-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-white">Password Protection</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Passwords are encrypted using PBKDF2/SHA256 password hashing and never stored in plain text.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start gap-4">
              <Lock className="h-5 w-5 text-indigo-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-white">Session Security</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Session keys are automatically regenerated upon login and invalidated when logging out.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start gap-4">
              <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-white">Account Deletion & Data Export</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Account deletion and multi-portfolio export functionality will be unlocked in Sprint 3.
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

