import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, Mail, Calendar, Shield, Save, Database } from 'lucide-react';
import { useCurrentUser, useUpdateProfile } from '@/features/authentication/hooks/useAuth';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Alert } from '@/shared/ui/Alert';

const profileSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(2, 'Full name must be at least 2 characters')
    .max(255, 'Full name cannot exceed 255 characters'),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export const ProfilePage: React.FC = () => {
  const { data: user } = useCurrentUser();
  const { mutate: updateProfile, isPending, error: mutationError } = useUpdateProfile();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: user?.full_name || '',
    },
  });

  const onSubmit = (values: ProfileFormValues) => {
    setSuccessMessage(null);
    updateProfile(values, {
      onSuccess: (updatedUser) => {
        setSuccessMessage('Profile name updated successfully.');
        reset({ full_name: updatedUser.full_name });
      },
    });
  };

  const formattedDate = user?.date_joined
    ? new Date(user.date_joined).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Recent';

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-theme-text">Profile Settings</h1>
        <p className="text-sm text-theme-text-muted">
          Manage your personal identity and account details across the platform.
        </p>
      </div>

      {successMessage && (
        <Alert variant="success" title="Success">
          {successMessage}
        </Alert>
      )}

      {mutationError && (
        <Alert variant="error" title="Update Failed">
          {mutationError.message || 'Unable to update profile. Please try again.'}
        </Alert>
      )}

      {/* Editable Profile Information */}
      <Card className="border-theme-border bg-theme-card p-6">
        <CardTitle className="text-lg text-theme-text mb-1">Personal Details</CardTitle>
        <CardDescription className="text-xs text-theme-text-muted mb-6">
          Your full name is used across dashboards, portfolio reports, and session headers.
        </CardDescription>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name" className="text-theme-text-secondary">
              Full Name
            </Label>
            <div className="relative">
              <Input
                id="full_name"
                type="text"
                disabled={isPending}
                placeholder="Enter your full name"
                className="bg-theme-surface border-theme-border text-theme-text pl-10"
                {...register('full_name')}
              />
              <User className="absolute left-3 top-3 h-4 w-4 text-theme-text-muted pointer-events-none" />
            </div>
            {errors.full_name && (
              <p className="text-xs text-theme-negative">{errors.full_name.message}</p>
            )}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button
              type="submit"
              disabled={isPending || !isDirty}
              className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm"
            >
              <Save className="mr-2 h-4 w-4" />
              {isPending ? 'Saving...' : 'Save Changes'}
            </Button>
            {isDirty && !isPending && (
              <span className="text-xs text-amber-400">Unsaved changes</span>
            )}
          </div>
        </form>
      </Card>

      {/* Read-Only Account Attributes */}
      <Card className="border-theme-border bg-theme-card p-6">
        <CardTitle className="text-lg text-theme-text mb-1">Account Credentials & Metadata</CardTitle>
        <CardDescription className="text-xs text-theme-text-muted mb-6">
          Verified system attributes maintained on the database.
        </CardDescription>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-theme-surface border border-theme-border space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              <Mail className="h-4 w-4 text-theme-primary" /> Registered Email
            </div>
            <div className="text-sm font-medium text-theme-text break-all">{user?.email}</div>
            <div className="text-[11px] text-theme-text-muted">
              Unique identifier used for authentication and login.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-theme-surface border border-theme-border space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              <Calendar className="h-4 w-4 text-theme-primary" /> Date Joined
            </div>
            <div className="text-sm font-medium text-theme-text">{formattedDate}</div>
            <div className="text-[11px] text-theme-text-muted">
              Stored in UTC on PostgreSQL (displayed in your timezone).
            </div>
          </div>

          <div className="p-4 rounded-lg bg-theme-surface border border-theme-border space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              <Shield className="h-4 w-4 text-theme-positive" /> Account ID (UUID)
            </div>
            <div className="text-xs font-mono text-theme-positive break-all">
              {user?.id || '—'}
            </div>
            <div className="text-[11px] text-theme-text-muted">
              Immutable primary key with UUIDv4 generation.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-theme-surface border border-theme-border space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-theme-text-muted uppercase tracking-wider">
              <Database className="h-4 w-4 text-theme-primary" /> Database Branch
            </div>
            <div className="text-sm font-medium text-theme-text">production (neondb)</div>
            <div className="text-[11px] text-theme-text-muted">
              Role: main_dev • AWS Singapore (ap-southeast-1).
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
