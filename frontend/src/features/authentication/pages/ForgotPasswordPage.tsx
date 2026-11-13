import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';

import { forgotPasswordSchema, ForgotPasswordFormData } from '../schemas/authSchemas';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Card } from '@/shared/ui/Card';
import { Alert } from '@/shared/ui/Alert';

export const ForgotPasswordPage: React.FC = () => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setServerError(null);
    setIsSubmitting(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 600));
      setSubmittedEmail(data.email);
      setIsSubmitted(true);
    } catch (err: any) {
      setServerError(err?.message || 'Unable to process your request. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full flex justify-center">
      <Card className="w-full max-w-[400px] border-theme-border bg-theme-card text-theme-text shadow-lg backdrop-blur-md p-6 sm:p-7">
        {!isSubmitted ? (
          <>
            <h1 className="text-xl font-bold tracking-tight text-theme-text mb-4">
              Forgot password?
            </h1>

            {serverError && (
              <div className="mb-4">
                <Alert variant="error" title="Request Failed">
                  {serverError}
                </Alert>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
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

              <Button
                type="submit"
                variant="primary"
                size="md"
                fullWidth
                isLoading={isSubmitting}
                className="mt-1 font-semibold"
              >
                Send Reset Link
              </Button>
            </form>

            <div className="mt-5 pt-4 border-t border-theme-border text-center text-xs">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 font-medium text-theme-primary hover:underline transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Back to Sign In</span>
              </Link>
            </div>
          </>
        ) : (
          <div className="text-center space-y-4 py-2">
            <div className="h-11 w-11 rounded-full bg-theme-primary/10 text-theme-primary border border-theme-primary/20 flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-6 w-6" />
            </div>

            <div>
              <h1 className="text-xl font-bold text-theme-text">Check your email</h1>
              <p className="text-xs text-theme-text-muted mt-1 leading-relaxed">
                A reset link has been dispatched to <span className="font-semibold text-theme-text">{submittedEmail}</span> if an account exists.
              </p>
            </div>

            <div className="pt-2 space-y-2.5">
              <Button
                variant="primary"
                size="md"
                fullWidth
                onClick={() => setIsSubmitted(false)}
              >
                Resend Email
              </Button>

              <div>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs font-medium text-theme-text-muted hover:text-theme-text transition-colors mt-1"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Return to Sign In</span>
                </Link>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
