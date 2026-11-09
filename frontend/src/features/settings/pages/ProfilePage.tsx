import React from 'react';
import { Link } from 'react-router-dom';
import { useCurrentUser } from '@/features/authentication/hooks/useAuth';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { ArrowLeft, User, Mail, Calendar, Shield } from 'lucide-react';

export const ProfilePage: React.FC = () => {
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
          <h1 className="text-2xl font-bold text-white">Profile Settings</h1>
          <p className="text-sm text-slate-400">Manage your personal details and account presence</p>
        </div>

        <Card className="border-slate-800 bg-slate-900 text-slate-100">
          <CardTitle className="text-lg text-white mb-1">User Information</CardTitle>
          <CardDescription className="text-xs text-slate-400 mb-6">
            Basic information verified during registration
          </CardDescription>

          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <User className="h-5 w-5 text-indigo-400" />
              <div>
                <div className="text-[11px] text-slate-400 uppercase tracking-wider">Full Name</div>
                <div className="text-sm font-medium text-white">{user?.full_name}</div>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <Mail className="h-5 w-5 text-indigo-400" />
              <div>
                <div className="text-[11px] text-slate-400 uppercase tracking-wider">Email Address</div>
                <div className="text-sm font-medium text-white">{user?.email}</div>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <Calendar className="h-5 w-5 text-indigo-400" />
              <div>
                <div className="text-[11px] text-slate-400 uppercase tracking-wider">Date Joined</div>
                <div className="text-sm font-medium text-white">
                  {user?.date_joined ? new Date(user.date_joined).toLocaleString() : 'N/A'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <Shield className="h-5 w-5 text-emerald-400" />
              <div>
                <div className="text-[11px] text-slate-400 uppercase tracking-wider">Authentication Strategy</div>
                <div className="text-sm font-medium text-emerald-300">Secure HTTP-only Session Cookie (Active)</div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
