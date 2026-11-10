import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Clock, Loader2, ArrowRight, TrendingUp } from 'lucide-react';
import { useVerifyEmail, useResendVerification, useCurrentUser } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';

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
          setResendError(err?.message || 'Failed to resend verification email.');
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg mb-3">
            <TrendingUp className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">Portfolio Manager</h1>
          <p className="text-xs text-slate-400 mt-1">Email Verification</p>
        </div>

        <Card className="border-slate-800 bg-slate-900/60 p-6 sm:p-8 backdrop-blur">
          {/* State: Verifying */}
          {(state === 'verifying' || isVerifying) && (
            <div className="text-center py-6 space-y-4">
              <Loader2 className="h-10 w-10 text-indigo-400 animate-spin mx-auto" />
              <div>
                <CardTitle className="text-lg text-white">Verifying your email...</CardTitle>
                <CardDescription className="text-xs text-slate-400 mt-1">
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
                <CardTitle className="text-xl text-white">Email Verified Successfully!</CardTitle>
                <CardDescription className="text-xs text-slate-400 mt-2">
                  Your email address has been confirmed. Your account now has full access to portfolio management features.
                </CardDescription>
              </div>
              <Button
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                onClick={() => navigate('/dashboard')}
              >
                Go to Dashboard <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}

          {/* State: Already Verified */}
          {state === 'already_verified' && !isVerifying && (
            <div className="text-center py-4 space-y-5">
              <div className="h-12 w-12 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <CardTitle className="text-xl text-white">Already Verified</CardTitle>
                <CardDescription className="text-xs text-slate-400 mt-2">
                  This account has already verified its email address.
                </CardDescription>
              </div>
              <Button
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                onClick={() => navigate('/dashboard')}
              >
                Go to Dashboard <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}

          {/* State: Expired */}
          {state === 'expired' && !isVerifying && (
            <div className="py-4 space-y-5">
              <div className="text-center space-y-3">
                <div className="h-12 w-12 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center mx-auto">
                  <Clock className="h-7 w-7" />
                </div>
                <div>
                  <CardTitle className="text-xl text-white">Verification Link Expired</CardTitle>
                  <CardDescription className="text-xs text-slate-400 mt-2">
                    Security tokens expire after 30 minutes. Enter your email below to receive a new link.
                  </CardDescription>
                </div>
              </div>

              {resendSuccess ? (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400 text-center">
                  A fresh verification link has been sent to your email address!
                </div>
              ) : (
                <form onSubmit={handleResend} className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">
                      Account Email
                    </label>
                    <Input
                      type="email"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                    />
                  </div>
                  {resendError && (
                    <div className="text-xs text-rose-400">{resendError}</div>
                  )}
                  <Button
                    type="submit"
                    disabled={isResending}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                  >
                    {isResending ? 'Sending...' : 'Request New Verification Link'}
                  </Button>
                </form>
              )}

              <div className="text-center pt-2">
                <Link to="/login" className="text-xs text-indigo-400 hover:text-indigo-300">
                  Return to Login
                </Link>
              </div>
            </div>
          )}

          {/* State: Invalid */}
          {state === 'invalid' && !isVerifying && (
            <div className="py-4 space-y-5">
              <div className="text-center space-y-3">
                <div className="h-12 w-12 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto">
                  <AlertCircle className="h-7 w-7" />
                </div>
                <div>
                  <CardTitle className="text-xl text-white">Invalid Verification Link</CardTitle>
                  <CardDescription className="text-xs text-slate-400 mt-2">
                    This verification token is invalid, malformed, or has already been used.
                  </CardDescription>
                </div>
              </div>

              {resendSuccess ? (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400 text-center">
                  A new verification link has been sent to your email.
                </div>
              ) : (
                <form onSubmit={handleResend} className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">
                      Send a new verification link
                    </label>
                    <Input
                      type="email"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                    />
                  </div>
                  {resendError && (
                    <div className="text-xs text-rose-400">{resendError}</div>
                  )}
                  <Button
                    type="submit"
                    disabled={isResending}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                  >
                    {isResending ? 'Sending...' : 'Send Verification Link'}
                  </Button>
                </form>
              )}

              <div className="text-center pt-2">
                <Link to="/login" className="text-xs text-indigo-400 hover:text-indigo-300">
                  Return to Login
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
