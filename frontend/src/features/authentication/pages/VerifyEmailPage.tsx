import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Clock, Loader2, ArrowRight, TrendingUp } from 'lucide-react';
import { useVerifyEmail, useResendVerification, useCurrentUser } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { ThemeToggle } from '@/design-system';

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { data: currentUser } = useCurrentUser();

  const { mutate: verifyEmail, isPending: isVerifying } = useVerifyEmail();
  const { mutate: resendVerification, isPending: isResending } = useResendVerification();

  const [state, setState] = useState<'verifying' | 'success' | 'already_verified' | 'expired' | 'invalid'>(
    token ? 'verifying' : 'invalid'
  );
  const [resendEmail, setResendEmail] = useState(currentUser?.email || '');
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState('');

  useEffect(() => {
    if (!token) {
      setState('invalid');
      return;
    }

    verifyEmail(
      { token },
      {
        onSuccess: (data) => {
          if (data.status === 'already_verified') {
            setState('already_verified');
          } else {
            setState('success');
          }
        },
        onError: (err: any) => {
          const code = err?.data?.code;
          if (code === 'expired') {
            setState('expired');
          } else {
            setState('invalid');
          }
        },
      }
    );
  }, [token, verifyEmail]);

  const handleResend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!resendEmail) return;

    setResendSuccess(false);
    setResendError('');

    resendVerification(
      { email: resendEmail },
      {
        onSuccess: () => {
          setResendSuccess(true);
        },
        onError: (err: any) => {
          setResendError(err.message || 'Failed to send verification link.');
        },
      }
    );
  };

  return (
    <div className="relative min-h-screen bg-theme-bg text-theme-text flex flex-col justify-center items-center p-4 transition-colors duration-200">
      {/* Top Right Floating Theme Switcher */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6 z-10">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-theme-primary text-theme-text-inverse shadow-md mb-3">
            <TrendingUp className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-theme-text">Portfolio Manager</h1>
          <p className="text-xs text-theme-text-muted mt-1">Email Verification</p>
        </div>

        <Card className="border-theme-border bg-theme-card text-theme-text p-6 sm:p-8 shadow-xl backdrop-blur-md">
          {/* State: Verifying */}
          {(state === 'verifying' || isVerifying) && (
            <div className="text-center py-6 space-y-4">
              <Loader2 className="h-10 w-10 text-theme-primary animate-spin mx-auto" />
              <div>
                <CardTitle className="text-lg text-theme-text">Verifying your email...</CardTitle>
                <CardDescription className="text-xs text-theme-text-muted mt-1">
                  Validating your cryptographic verification token.
                </CardDescription>
              </div>
            </div>
          )}

          {/* State: Success */}
          {state === 'success' && !isVerifying && (
            <div className="text-center py-4 space-y-5">
              <div className="h-12 w-12 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <CardTitle className="text-xl text-theme-text">Email Verified Successfully!</CardTitle>
                <CardDescription className="text-xs text-theme-text-muted mt-2">
                  Your email address has been confirmed. Your account now has full access to portfolio management features.
                </CardDescription>
              </div>
              <Button
                variant="primary"
                fullWidth
                onClick={() => navigate('/dashboard')}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Go to Dashboard
              </Button>
            </div>
          )}

          {/* State: Already Verified */}
          {state === 'already_verified' && !isVerifying && (
            <div className="text-center py-4 space-y-5">
              <div className="h-12 w-12 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <CardTitle className="text-xl text-theme-text">Already Verified</CardTitle>
                <CardDescription className="text-xs text-theme-text-muted mt-2">
                  This account has already verified its email address.
                </CardDescription>
              </div>
              <Button
                variant="primary"
                fullWidth
                onClick={() => navigate('/dashboard')}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Go to Dashboard
              </Button>
            </div>
          )}

          {/* State: Expired */}
          {state === 'expired' && !isVerifying && (
            <div className="space-y-5">
              <div className="text-center space-y-2">
                <div className="h-12 w-12 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center mx-auto mb-2">
                  <Clock className="h-7 w-7" />
                </div>
                <CardTitle className="text-xl text-theme-text">Link Expired</CardTitle>
                <CardDescription className="text-xs text-theme-text-muted">
                  This verification link has expired. Verification links are time-limited for security.
                </CardDescription>
              </div>

              {resendSuccess ? (
                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-center">
                  <p className="text-xs text-emerald-400 font-medium">
                    A fresh verification link has been sent to your email.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleResend} className="space-y-3 pt-2">
                  <div>
                    <label htmlFor="resend-email" className="block text-xs font-medium text-theme-text-secondary mb-1">
                      Send a new verification link to:
                    </label>
                    <Input
                      id="resend-email"
                      type="email"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      placeholder="your.email@example.com"
                      required
                      className="bg-theme-surface border-theme-border text-theme-text placeholder:text-theme-text-muted"
                    />
                  </div>
                  {resendError && (
                    <p className="text-xs text-rose-400">{resendError}</p>
                  )}
                  <Button
                    type="submit"
                    variant="primary"
                    fullWidth
                    isLoading={isResending}
                  >
                    Resend Verification Email
                  </Button>
                </form>
              )}

              <div className="text-center pt-2">
                <Link to="/login" className="text-xs text-theme-text-muted hover:text-theme-text">
                  Back to Sign In
                </Link>
              </div>
            </div>
          )}

          {/* State: Invalid */}
          {state === 'invalid' && !isVerifying && (
            <div className="space-y-5">
              <div className="text-center space-y-2">
                <div className="h-12 w-12 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto mb-2">
                  <AlertCircle className="h-7 w-7" />
                </div>
                <CardTitle className="text-xl text-theme-text">Invalid Verification Link</CardTitle>
                <CardDescription className="text-xs text-theme-text-muted">
                  This verification link is invalid or malformed.
                </CardDescription>
              </div>

              {resendSuccess ? (
                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-center">
                  <p className="text-xs text-emerald-400 font-medium">
                    A fresh verification link has been sent to your email.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleResend} className="space-y-3 pt-2">
                  <div>
                    <label htmlFor="resend-email-invalid" className="block text-xs font-medium text-theme-text-secondary mb-1">
                      Request a verification email:
                    </label>
                    <Input
                      id="resend-email-invalid"
                      type="email"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      placeholder="your.email@example.com"
                      required
                      className="bg-theme-surface border-theme-border text-theme-text placeholder:text-theme-text-muted"
                    />
                  </div>
                  {resendError && (
                    <p className="text-xs text-rose-400">{resendError}</p>
                  )}
                  <Button
                    type="submit"
                    variant="primary"
                    fullWidth
                    isLoading={isResending}
                  >
                    Send Verification Email
                  </Button>
                </form>
              )}

              <div className="text-center pt-2">
                <Link to="/login" className="text-xs text-theme-text-muted hover:text-theme-text">
                  Back to Sign In
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
