import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  LogOut,
  Mail,
  CheckCircle2,
  AlertCircle,
  Send,
} from 'lucide-react';
import { useCurrentUser, useLogout, useResendVerification } from '@/features/authentication/hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import styles from './Settings.module.css';

export const AccountPage: React.FC = () => {
  const { data: user } = useCurrentUser();
  const { mutate: logout, isPending: isLoggingOut } = useLogout();
  const { mutate: resendVerification, isPending: isResending } = useResendVerification();
  const [resendStatus, setResendStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [resendMessage, setResendMessage] = useState<string>('');
  const navigate = useNavigate();

  const handleLogout = () => {
    logout(undefined, {
      onSuccess: () => {
        navigate('/login', { replace: true });
      },
    });
  };

  const handleResendVerification = () => {
    if (!user?.email) return;
    setResendStatus('idle');
    setResendMessage('');

    resendVerification(
      { email: user.email },
      {
        onSuccess: (data) => {
          setResendStatus('success');
          setResendMessage(data.message || 'Verification email has been sent. Check your inbox.');
        },
        onError: (err: any) => {
          setResendStatus('error');
          setResendMessage(err?.message || 'Failed to send verification email. Please try again later.');
        },
      }
    );
  };

  const isEmailVerified = Boolean(user?.is_email_verified);

  return (
    <div className={styles.container}>
      {/* 1. Page Header */}
      <header className={styles.headerRow}>
        <h1 className={styles.title}>Account Settings</h1>
        <p className={styles.subtitle}>
          Manage your account security, authentication credentials, and active sessions.
        </p>
      </header>

      {/* 2. Account Overview Card */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>Account & Verification Status</h2>
          <p className={styles.cardDescription}>
            Real system verification and credential status.
          </p>
        </div>

        <div className="space-y-4">
          {/* Registered Email & Verification */}
          <div className="p-4 rounded-lg bg-theme-bg border border-theme-border space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-theme-primary" />
                <div>
                  <div className="text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
                    Registered Email
                  </div>
                  <div className="text-sm font-medium text-theme-text">{user?.email}</div>
                </div>
              </div>
              <div>
                {isEmailVerified ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20">
                    <AlertCircle className="h-3.5 w-3.5" /> Unverified
                  </span>
                )}
              </div>
            </div>

            {/* Unverified Action State */}
            {!isEmailVerified && (
              <div className="pt-2 border-t border-theme-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="text-xs text-amber-400/90">
                  Your email address requires confirmation to unlock advanced notification alerts.
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleResendVerification}
                  isLoading={isResending}
                  className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 shrink-0"
                >
                  <Send className="mr-1.5 h-3.5 w-3.5" /> Resend verification link
                </Button>
              </div>
            )}

            {/* Feedback notification */}
            {resendStatus !== 'idle' && (
              <div
                className={`p-3 rounded-lg text-xs ${
                  resendStatus === 'success'
                    ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/10 border border-rose-500/20 text-rose-300'
                }`}
              >
                {resendMessage}
              </div>
            )}
          </div>

          {/* Account Status */}
          <div className={styles.infoRow}>
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-theme-primary" />
              <div>
                <div className={styles.infoLabel}>Account State</div>
                <div className={styles.infoValue}>Active</div>
              </div>
            </div>
            <span className="text-xs text-theme-text-muted">Standard Member</span>
          </div>
        </div>
      </div>

      {/* 3. Session & Security Actions */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>Session & Security</h2>
          <p className={styles.cardDescription}>
            Sign out of your active session or manage device access.
          </p>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div>
            <div className="text-sm font-medium text-theme-text">Sign out of this session</div>
            <div className="text-xs text-theme-text-muted mt-0.5">
              Terminates your secure HTTP-only refresh tokens.
            </div>
          </div>
          <Button
            variant="danger"
            size="sm"
            onClick={handleLogout}
            isLoading={isLoggingOut}
          >
            <LogOut className="mr-1.5 h-3.5 w-3.5" /> Sign Out
          </Button>
        </div>
      </div>
    </div>
  );
};
