import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail } from 'lucide-react';

import { loginSchema, LoginFormData } from '../schemas/authSchemas';
import { useLogin } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Card } from '@/shared/ui/Card';
import { Alert } from '@/shared/ui/Alert';
import { GoogleIcon } from '@/shared/ui/GoogleIcon';

export const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [oauthNotice, setOauthNotice] = useState<string | null>(null);

  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/dashboard';

  const { mutate: login, isPending } = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = (data: LoginFormData) => {
    setServerError(null);
    setOauthNotice(null);
    login(data, {
      onSuccess: () => {
        navigate(from, { replace: true });
      },
      onError: (err: any) => {
        setServerError(err.message || 'Unable to log in. Please verify your credentials.');
      },
    });
  };

  const handleGoogleSignIn = () => {
    setOauthNotice('Google Authentication is enabled in the authentication scope and will be connected to the backend OAuth provider.');
  };

  return (
    <div className="w-full flex justify-center">
      <Card className="w-full max-w-[400px] border-theme-border bg-theme-card text-theme-text shadow-lg backdrop-blur-md p-6 sm:p-7">
        <h1 className="text-xl font-bold tracking-tight text-theme-text mb-4">
          Welcome back
        </h1>

        {oauthNotice && (
          <div className="mb-4">
            <Alert variant="info" title="Google Authentication">
              {oauthNotice}
            </Alert>
          </div>
        )}

        {serverError && (
          <div className="mb-4">
            <Alert variant="error" title="Authentication Error">
              {serverError}
            </Alert>
          </div>
        )}

        {/* Google Sign In */}
        <Button
          type="button"
          variant="secondary"
          size="md"
          fullWidth
          onClick={handleGoogleSignIn}
          leftIcon={<GoogleIcon size={18} />}
          className="font-medium text-sm border-theme-border text-theme-text hover:bg-theme-surface-hover"
        >
          Continue with Google
        </Button>

        {/* Minimal Divider */}
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-theme-border" />
          </div>
          <div className="relative flex justify-center text-2xs uppercase">
            <span className="bg-theme-card px-2.5 text-theme-text-muted font-medium tracking-wider">
              Or continue with email
            </span>
          </div>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5" noValidate>
          <div>
            <Label htmlFor="email" required className="text-xs font-medium text-theme-text-secondary mb-1">
              Email Address
            </Label>
            <Input
              id="email"
              type="email"
              size="md"
              autoComplete="email"
              placeholder="name@example.com"
              leftIcon={<Mail className="h-4 w-4 text-theme-text-muted" />}
              error={errors.email?.message}
              {...register('email')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <Label htmlFor="password" required className="text-xs font-medium text-theme-text-secondary mb-0">
                Password
              </Label>
              <Link
                to="/forgot-password"
                className="text-xs font-medium text-theme-primary hover:underline transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              size="md"
              autoComplete="current-password"
              placeholder="••••••••"
              leftIcon={<Lock className="h-4 w-4 text-theme-text-muted" />}
              rightIcon={
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-theme-text-muted hover:text-theme-text transition-colors p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              error={errors.password?.message}
              {...register('password')}
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            fullWidth
            isLoading={isPending}
            className="mt-1 font-semibold"
          >
            Sign In
          </Button>
        </form>

        {/* Minimal Footer */}
        <div className="mt-5 pt-4 border-t border-theme-border text-center text-xs text-theme-text-muted">
          Don't have an account yet?{' '}
          <Link
            to="/register"
            className="font-semibold text-theme-primary hover:underline transition-colors"
          >
            Create an account
          </Link>
        </div>
      </Card>
    </div>
  );
};
