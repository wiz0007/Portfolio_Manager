import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail, User, TrendingUp } from 'lucide-react';

import { registerSchema, RegisterFormData } from '../schemas/authSchemas';
import { useRegister } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Card, CardHeader, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Alert } from '@/shared/ui/Alert';
import { ThemeToggle } from '@/design-system';

export const RegisterPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const navigate = useNavigate();
  const { mutate: registerUser, isPending } = useRegister();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      password_confirmation: '',
    },
  });

  const onSubmit = (data: RegisterFormData) => {
    setServerError(null);
    registerUser(data, {
      onSuccess: () => {
        navigate('/dashboard', { replace: true });
      },
      onError: (err: any) => {
        if (err.data && typeof err.data === 'object') {
          if (err.data.email) {
            setServerError(Array.isArray(err.data.email) ? err.data.email.join(' ') : String(err.data.email));
            return;
          }
          if (err.data.password) {
            setServerError(Array.isArray(err.data.password) ? err.data.password.join(' ') : String(err.data.password));
            return;
          }
        }
        setServerError(err.message || 'Registration failed. Please check your details and try again.');
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
          Start tracking your multi-asset wealth today
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="border-theme-border bg-theme-card text-theme-text shadow-xl backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-xl text-theme-text">Create an account</CardTitle>
            <CardDescription className="text-theme-text-muted">
              Enter your information to begin monitoring your assets
            </CardDescription>
          </CardHeader>

          {serverError && (
            <div className="mb-6">
              <Alert variant="error" title="Registration Error">
                {serverError}
              </Alert>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div>
              <Label htmlFor="full_name" required className="text-theme-text-secondary">
                Full Name
              </Label>
              <div className="relative">
                <Input
                  id="full_name"
                  type="text"
                  autoComplete="name"
                  placeholder="John Doe"
                  error={errors.full_name?.message}
                  {...register('full_name')}
                  className="bg-theme-surface border-theme-border text-theme-text placeholder:text-theme-text-muted pl-10 focus:border-theme-primary"
                />
                <User className="absolute left-3 top-2.5 h-5 w-5 text-theme-text-muted pointer-events-none" />
              </div>
            </div>

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
              <Label htmlFor="password" required className="text-theme-text-secondary">
                Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="Minimum 8 characters"
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

            <div>
              <Label htmlFor="password_confirmation" required className="text-theme-text-secondary">
                Confirm Password
              </Label>
              <div className="relative">
                <Input
                  id="password_confirmation"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="Repeat your password"
                  error={errors.password_confirmation?.message}
                  {...register('password_confirmation')}
                  className="bg-theme-surface border-theme-border text-theme-text placeholder:text-theme-text-muted pl-10 pr-10 focus:border-theme-primary"
                />
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-theme-text-muted pointer-events-none" />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-2.5 text-theme-text-muted hover:text-theme-text transition-colors"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              fullWidth
              isLoading={isPending}
              className="mt-4 font-semibold"
            >
              Create Account
            </Button>
          </form>

          <div className="mt-6 border-t border-theme-border pt-5 text-center text-sm text-theme-text-muted">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-medium text-theme-primary hover:underline transition-colors"
            >
              Sign In
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
