import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, Mail, Calendar, Save } from 'lucide-react';
import { useCurrentUser, useUpdateProfile } from '@/features/authentication/hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';
import { Alert } from '@/shared/ui/Alert';
import styles from './Settings.module.css';

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
      })
    : 'Recent';

  return (
    <div className={styles.container}>
      {/* 1. Page Header */}
      <header className={styles.headerRow}>
        <h1 className={styles.title}>Profile Settings</h1>
        <p className={styles.subtitle}>
          Manage your personal identity across the platform.
        </p>
      </header>

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

      {/* 2. Editable Profile Information */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>Personal Details</h2>
          <p className={styles.cardDescription}>
            Your full name is used on dashboards and portfolio reports.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.formGrid}>
          <div className={styles.formGroup}>
            <Label htmlFor="full_name" required className="text-theme-text-secondary text-xs">
              Full Name
            </Label>
            <div className={styles.inputIconWrapper}>
              <User className={styles.inputIcon} />
              <Input
                id="full_name"
                type="text"
                disabled={isPending}
                placeholder="Enter your full name"
                className={styles.iconInput}
                error={errors.full_name?.message}
                {...register('full_name')}
              />
            </div>
          </div>

          <div className={styles.formActions}>
            <Button
              type="submit"
              size="sm"
              isLoading={isPending}
              disabled={!isDirty || isPending}
              className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm"
            >
              <Save className="mr-1.5 h-3.5 w-3.5" /> Save Changes
            </Button>
          </div>
        </form>
      </div>

      {/* 3. Read-only Account Identity */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>Identity & Registration</h2>
          <p className={styles.cardDescription}>
            Account metadata established during registration.
          </p>
        </div>

        <div className="space-y-3">
          <div className={styles.infoRow}>
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-theme-primary" />
              <div>
                <div className={styles.infoLabel}>Email Address</div>
                <div className={styles.infoValue}>{user?.email || '—'}</div>
              </div>
            </div>
            <span className="text-xs text-theme-text-muted">Primary identifier</span>
          </div>

          <div className={styles.infoRow}>
            <div className="flex items-center gap-3">
              <Calendar className="h-4 w-4 text-theme-primary" />
              <div>
                <div className={styles.infoLabel}>Member Since</div>
                <div className={styles.infoValue}>{formattedDate}</div>
              </div>
            </div>
            <span className="text-xs text-theme-text-muted">Registration timestamp</span>
          </div>
        </div>
      </div>
    </div>
  );
};
