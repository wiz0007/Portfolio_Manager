import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail, User as UserIcon, TrendingUp, CheckCircle2 } from 'lucide-react';

import { registerSchema, RegisterFormData } from '../schemas/authSchemas';
import { useRegister } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Card, CardHeader, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Alert } from '@/shared/ui/Alert';

export const RegisterPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const navigate = useNavigate();
  const { mutate: registerUser, isPending } = useRegister();

  const {
    register,
    handleSubmit,
    watch,
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

  const passwordValue = watch('password', '');
  const hasMinLength = passwordValue.length >= 8;

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
    <div className="flex min-h-screen flex-col justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 px-4 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-lg">
            <TrendingUp className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-white">
            Portfolio Manager
          </span>
        </div>
        <p className="text-center text-sm text-slate-400">
          Start tracking your multi-asset wealth today
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="border-slate-700 bg-slate-900/90 text-slate-100 shadow-2xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-xl text-white">Create an account</CardTitle>
            <CardDescription className="text-slate-400">
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
              <Label htmlFor="full_name" required className="text-slate-300">
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
                  className="bg-slate-800/80 border-slate-700 text-white placeholder:text-slate-500 pl-10 focus:border-indigo-500"
                />
                <UserIcon className="absolute left-3 top-2.5 h-5 w-5 text-slate-500 pointer-events-none" />
              </div>
            </div>

            <div>
              <Label htmlFor="email" required className="text-slate-300">
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
                  className="bg-slate-800/80 border-slate-700 text-white placeholder:text-slate-500 pl-10 focus:border-indigo-500"
                />
                <Mail className="absolute left-3 top-2.5 h-5 w-5 text-slate-500 pointer-events-none" />
              </div>
            </div>

            <div>
              <Label htmlFor="password" required className="text-slate-300">
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
                  className="bg-slate-800/80 border-slate-700 text-white placeholder:text-slate-500 pl-10 pr-10 focus:border-indigo-500"
                />
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-slate-500 pointer-events-none" />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>

              {passwordValue && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
                  <CheckCircle2
                    className={`h-4 w-4 ${hasMinLength ? 'text-emerald-400' : 'text-slate-600'}`}
                  />
                  <span className={hasMinLength ? 'text-slate-300' : 'text-slate-500'}>
                    At least 8 characters
                  </span>
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="password_confirmation" required className="text-slate-300">
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
                  className="bg-slate-800/80 border-slate-700 text-white placeholder:text-slate-500 pl-10 pr-10 focus:border-indigo-500"
                />
                <Lock className="absolute left-3 top-2.5 h-5 w-5 text-slate-500 pointer-events-none" />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200 transition-colors"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              isLoading={isPending}
              className="w-full mt-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 shadow-indigo-600/30"
            >
              Create Account
            </Button>
          </form>

          <div className="mt-6 border-t border-slate-800 pt-5 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors underline-offset-4 hover:underline"
            >
              Sign in
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

