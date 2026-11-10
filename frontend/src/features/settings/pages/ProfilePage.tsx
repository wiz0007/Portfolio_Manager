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
        <h1 className="text-2xl font-bold tracking-tight text-white">Profile Settings</h1>
        <p className="text-sm text-slate-400">
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
      <Card className="border-slate-800 bg-slate-900/60 p-6">
        <CardTitle className="text-lg text-white mb-1">Personal Details</CardTitle>
        <CardDescription className="text-xs text-slate-400 mb-6">
          Your full name is used across dashboards, portfolio reports, and session headers.
        </CardDescription>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name" className="text-slate-300">
              Full Name
            </Label>
            <div className="relative">
              <Input
                id="full_name"
                type="text"
                disabled={isPending}
                placeholder="Enter your full name"
                className="bg-slate-950 border-slate-700 text-white pl-10"
                {...register('full_name')}
              />
              <User className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
            </div>
            {errors.full_name && (
              <p className="text-xs text-rose-400">{errors.full_name.message}</p>
            )}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button
              type="submit"
              disabled={isPending || !isDirty}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
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
      <Card className="border-slate-800 bg-slate-900/60 p-6">
        <CardTitle className="text-lg text-white mb-1">Account Credentials & Metadata</CardTitle>
        <CardDescription className="text-xs text-slate-400 mb-6">
          Verified system attributes maintained on the Neon PostgreSQL database.
        </CardDescription>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <Mail className="h-4 w-4 text-indigo-400" /> Registered Email
            </div>
            <div className="text-sm font-medium text-white break-all">{user?.email}</div>
            <div className="text-[11px] text-slate-500">
              Unique identifier used for authentication and login.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <Calendar className="h-4 w-4 text-indigo-400" /> Date Joined
            </div>
            <div className="text-sm font-medium text-white">{formattedDate}</div>
            <div className="text-[11px] text-slate-500">
              Stored in UTC on PostgreSQL (displayed in your timezone).
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <Shield className="h-4 w-4 text-emerald-400" /> Account ID (UUID)
            </div>
            <div className="text-xs font-mono text-emerald-300 break-all">
              {user?.id || '—'}
            </div>
            <div className="text-[11px] text-slate-500">
              Immutable primary key with UUIDv4 generation.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <Database className="h-4 w-4 text-indigo-400" /> Database Branch
            </div>
            <div className="text-sm font-medium text-white">production (neondb)</div>
            <div className="text-[11px] text-slate-500">
              Role: main_dev • AWS Singapore (ap-southeast-1).
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
