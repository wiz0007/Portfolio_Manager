import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail, User } from 'lucide-react';

import { registerSchema, RegisterFormData } from '../schemas/authSchemas';
import { useRegister } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Card } from '@/shared/ui/Card';
import { Alert } from '@/shared/ui/Alert';
import { GoogleAuthButton } from '../components/GoogleAuthButton';

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
    <div className="w-full flex justify-center">
      <Card className="w-full max-w-[420px] border-theme-border bg-theme-card text-theme-text shadow-lg backdrop-blur-md p-6 sm:p-7">
        <h1 className="text-xl font-bold tracking-tight text-theme-text mb-4">
          Create an account
        </h1>

        {serverError && (
          <div className="mb-4">
            <Alert variant="error" title="Registration Error">
              {serverError}
            </Alert>
          </div>
        )}

        {/* Google Sign Up */}
        <GoogleAuthButton mode="signup" onError={(err) => setServerError(err)} />

        {/* Minimal Divider */}
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-theme-border" />
          </div>
          <div className="relative flex justify-center text-2xs uppercase">
            <span className="bg-theme-card px-2.5 text-theme-text-muted font-medium tracking-wider">
              Or register with email
            </span>
          </div>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3" noValidate>
          <div>
            <Label htmlFor="full_name" required className="text-xs font-medium text-theme-text-secondary mb-1">
              Full Name
            </Label>
            <Input
              id="full_name"
              type="text"
              size="md"
              autoComplete="name"
              placeholder="John Doe"
              leftIcon={<User className="h-4 w-4 text-theme-text-muted" />}
              error={errors.full_name?.message}
              {...register('full_name')}
            />
          </div>

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
            <Label htmlFor="password" required className="text-xs font-medium text-theme-text-secondary mb-1">
              Password
            </Label>
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              size="md"
              autoComplete="new-password"
              placeholder="Minimum 8 characters"
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

          <div>
            <Label htmlFor="password_confirmation" required className="text-xs font-medium text-theme-text-secondary mb-1">
              Confirm Password
            </Label>
            <Input
              id="password_confirmation"
              type={showConfirmPassword ? 'text' : 'password'}
              size="md"
              autoComplete="new-password"
              placeholder="Repeat your password"
              leftIcon={<Lock className="h-4 w-4 text-theme-text-muted" />}
              rightIcon={
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="text-theme-text-muted hover:text-theme-text transition-colors p-1"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
              error={errors.password_confirmation?.message}
              {...register('password_confirmation')}
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
            Create Account
          </Button>
        </form>

        {/* Minimal Footer */}
        <div className="mt-5 pt-4 border-t border-theme-border text-center text-xs text-theme-text-muted">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold text-theme-primary hover:underline transition-colors"
          >
            Sign In
          </Link>
        </div>
      </Card>
    </div>
  );
};
