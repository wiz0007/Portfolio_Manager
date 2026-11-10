import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  LogOut,
  Mail,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { useCurrentUser, useLogout } from '@/features/authentication/hooks/useAuth';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';

export const AccountPage: React.FC = () => {
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

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Account Settings</h1>
        <p className="text-sm text-slate-400">
          Manage your account security, authentication credentials, and active sessions.
        </p>
      </div>

      {/* Account Overview Card */}
      <Card className="border-slate-800 bg-slate-900/60 p-6">
        <CardTitle className="text-lg text-white mb-1">Account Status</CardTitle>
        <CardDescription className="text-xs text-slate-400 mb-6">
          System verification and security status.
        </CardDescription>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-indigo-400" />
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Registered Email
                </div>
                <div className="text-sm font-medium text-white">{user?.email}</div>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-3.5 w-3.5" /> Active & Verified
            </span>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-cyan-400" />
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Session Authentication
                </div>
                <div className="text-sm font-medium text-white">HTTP-Only Cookie with CSRF Defense</div>
              </div>
            </div>
            <span className="text-xs text-slate-400 font-mono">sessionid active</span>
          </div>
        </div>
      </Card>

      {/* Security & Password Policy Card */}
      <Card className="border-slate-800 bg-slate-900/60 p-6">
        <CardTitle className="text-lg text-white mb-1">Password & Authentication</CardTitle>
        <CardDescription className="text-xs text-slate-400 mb-6">
          Password hashing uses PBKDF2 with SHA256 iterations.
        </CardDescription>

        <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-3">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-medium text-white">
                Password Change & Multi-Factor Authentication
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Self-service password rotation, email verification links, and 2FA will be delivered in upcoming security enhancements.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Session Management & Logout */}
      <Card className="border-rose-950/40 bg-slate-900/60 p-6">
        <CardTitle className="text-lg text-white mb-1">Session Management</CardTitle>
        <CardDescription className="text-xs text-slate-400 mb-4">
          Terminate your current authenticated session and flush session cookies.
        </CardDescription>

        <div className="flex items-center justify-between p-4 rounded-lg bg-slate-950/60 border border-slate-800">
          <div>
            <div className="text-sm font-medium text-white">Sign Out from this Browser</div>
            <div className="text-xs text-slate-500">
              Clears the session cookie from the browser and destroys the server-side session.
            </div>
          </div>

          <Button
            variant="danger"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="bg-rose-600 hover:bg-rose-700 text-white shrink-0 ml-4"
          >
            <LogOut className="mr-2 h-4 w-4" />
            {isLoggingOut ? 'Signing out...' : 'Sign Out'}
          </Button>
        </div>
      </Card>
    </div>
  );
};
