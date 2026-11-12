import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail, TrendingUp } from 'lucide-react';

import { loginSchema, LoginFormData } from '../schemas/authSchemas';
import { useLogin } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Card, CardHeader, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Alert } from '@/shared/ui/Alert';
import { ThemeToggle } from '@/design-system';

export const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

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
    login(data, {
      onSuccess: () => {
        navigate(from, { replace: true });
      },
      onError: (err: any) => {
        setServerError(err.message || 'Unable to log in. Please verify your credentials.');
      },
    });
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center bg-theme-bg text-theme-text px-4 py-12 sm:px-6 lg:px-8 transition-colors duration-200">
      {/* Top Right Floating Theme Switcher */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6 z-10">
        <ThemeToggle />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex items-center justify-center gap-2.5 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-theme-primary text-theme-text-inverse shadow-md">
            <TrendingUp className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-theme-text">
            Portfolio Manager
          </span>
        </div>
        <p className="text-center text-sm text-theme-text-muted">
          Intelligent multi-asset wealth monitoring
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="border-theme-border bg-theme-card text-theme-text shadow-xl backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-xl text-theme-text">Welcome back</CardTitle>
            <CardDescription className="text-theme-text-muted">
              Sign in to manage and analyze your portfolios
            </CardDescription>
          </CardHeader>

          {serverError && (
            <div className="mb-6">
              <Alert variant="error" title="Authentication Error">
                {serverError}
              </Alert>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div>
              <Label htmlFor="email" required className="text-theme-text-secondary">
                Email Address
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="name@example.com"
                  error={errors.email?.message}
                  {...register('email')}
                  className="bg-theme-surface border-theme-border text-theme-text placeholder:text-theme-text-muted pl-10 focus:border-theme-primary"
                />
                <Mail className="absolute left-3 top-2.5 h-5 w-5 text-theme-text-muted pointer-events-none" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <Label htmlFor="password" required className="text-theme-text-secondary">
                  Password
                </Label>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  error={errors.password?.message}
                  {...register('password')}
                  className="bg-theme-surface border-theme-border text-theme-text placeholder:text-theme-text-muted pl-10 pr-10 focus:border-theme-primary"
                />
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-theme-text-muted pointer-events-none" />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-theme-text-muted hover:text-theme-text transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              fullWidth
              isLoading={isPending}
              className="mt-2 font-semibold"
            >
              Sign In
            </Button>
          </form>

          <div className="mt-6 border-t border-theme-border pt-5 text-center text-sm text-theme-text-muted">
            Don't have an account yet?{' '}
            <Link
              to="/register"
              className="font-medium text-theme-primary hover:underline transition-colors"
            >
              Create an account
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
