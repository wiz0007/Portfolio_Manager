import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  savingsAccountSchema,
  SavingsAccountFormData,
  SavingsAccountInput,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
  PercentageInput,
  DatePicker,
  SearchSelect,
  FormSection,
  FormActions,
} from '@/shared/components/forms';
import styles from '../forms.module.css';

const BANK_OPTIONS = [
  { value: 'State Bank of India', label: 'State Bank of India (SBI)' },
  { value: 'HDFC Bank', label: 'HDFC Bank' },
  { value: 'ICICI Bank', label: 'ICICI Bank' },
  { value: 'Axis Bank', label: 'Axis Bank' },
  { value: 'Kotak Mahindra Bank', label: 'Kotak Mahindra Bank' },
  { value: 'Punjab National Bank', label: 'Punjab National Bank (PNB)' },
  { value: 'Bank of Baroda', label: 'Bank of Baroda' },
  { value: 'Canara Bank', label: 'Canara Bank' },
  { value: 'Union Bank of India', label: 'Union Bank of India' },
  { value: 'IDFC FIRST Bank', label: 'IDFC FIRST Bank' },
  { value: 'AU Small Finance Bank', label: 'AU Small Finance Bank' },
  { value: 'Other Bank', label: 'Other Bank / Financial Institution' },
];

const ACCOUNT_TYPE_OPTIONS = [
  { value: 'SAVINGS', label: 'Regular Savings Account' },
  { value: 'SALARY', label: 'Corporate Salary Account' },
  { value: 'SENIOR_CITIZEN', label: 'Senior Citizen Savings' },
  { value: 'NRE_NRO', label: 'NRE / NRO Account' },
];

export interface SavingsAccountFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<SavingsAccountFormData>;
  onSubmit: (data: SavingsAccountFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const SavingsAccountForm: React.FC<SavingsAccountFormProps> = ({
  portfolioId,
  defaultCurrency = 'INR',
  initialValues,
  onSubmit,
  onBack,
  isSubmitting = false,
}) => {
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<SavingsAccountInput, any, SavingsAccountFormData>({
    resolver: zodResolver(savingsAccountSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      currency: (initialValues?.currency || defaultCurrency) as any,
      bank_name: initialValues?.bank_name || '',
      account_nickname: initialValues?.account_nickname || '',
      account_type: initialValues?.account_type || 'SAVINGS',
      masked_account_number: initialValues?.masked_account_number || '',
      current_balance: initialValues?.current_balance ?? 0,
      balance_date: initialValues?.balance_date || new Date().toISOString().split('T')[0],
      interest_rate_pct: initialValues?.interest_rate_pct ?? 3.0,
      interest_credit_frequency: initialValues?.interest_credit_frequency || 'QUARTERLY',
      auto_sweep_enabled: initialValues?.auto_sweep_enabled ?? false,
      sweep_out_threshold: initialValues?.sweep_out_threshold,
      sweep_retained_balance: initialValues?.sweep_retained_balance,
      sweep_increment: initialValues?.sweep_increment,
      notes: initialValues?.notes || '',
    },
  });

  const autoSweepEnabled = watch('auto_sweep_enabled');
  const currency = watch('currency') || 'INR';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Account Details"
        description="Select the banking institution and specify your account identification."
        columns={2}
      >
        <Controller
          name="bank_name"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="Bank / Financial Institution"
              options={BANK_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              error={errors.bank_name?.message}
              required
              placeholder="Search or enter bank..."
            />
          )}
        />

        <FormField
          label="Account Nickname"
          htmlFor="account_nickname"
          required
          error={errors.account_nickname?.message}
          helperText="e.g. Primary Salary A/C, Emergency Fund"
        >
          <input
            id="account_nickname"
            type="text"
            className={styles.textInput}
            placeholder="e.g. HDFC Salary"
            {...register('account_nickname')}
          />
        </FormField>

        <FormField
          label="Account Type"
          htmlFor="account_type"
          required
          error={errors.account_type?.message}
        >
          <select id="account_type" className={styles.selectInput} {...register('account_type')}>
            {ACCOUNT_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </FormField>

        <FormField
          label="Last 4 Digits / Masked A/C"
          htmlFor="masked_account_number"
          optional
          error={errors.masked_account_number?.message}
          helperText="For your visual identification only"
        >
          <input
            id="masked_account_number"
            type="text"
            className={styles.textInput}
            placeholder="e.g. XX1234"
            maxLength={10}
            {...register('masked_account_number')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Balance & Interest Terms"
        description="Current liquid balance and applicable bank rate."
        columns={2}
      >
        <Controller
          name="current_balance"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Current Balance"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.current_balance?.message}
              required
            />
          )}
        />

        <Controller
          name="balance_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Balance Effective Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.balance_date?.message}
              required
            />
          )}
        />

        <Controller
          name="interest_rate_pct"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="Annual Savings Interest Rate"
              value={field.value}
              onChange={field.onChange}
              error={errors.interest_rate_pct?.message}
              optional
              helperText="Typical Indian rates: 2.70% - 3.50%"
            />
          )}
        />

        <FormField
          label="Interest Credit Frequency"
          htmlFor="interest_credit_frequency"
          error={errors.interest_credit_frequency?.message}
        >
          <select
            id="interest_credit_frequency"
            className={styles.selectInput}
            {...register('interest_credit_frequency')}
          >
            <option value="QUARTERLY">Quarterly (RBI Standard)</option>
            <option value="MONTHLY">Monthly</option>
            <option value="HALF_YEARLY">Half Yearly</option>
            <option value="ANNUALLY">Annually</option>
          </select>
        </FormField>
      </FormSection>

      <FormSection
        title="Auto-Sweep Facility (Optional)"
        description="Configure automated sweep-in / sweep-out thresholds if linked to an FD pool."
        columns={1}
      >
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            className={styles.checkboxInput}
            {...register('auto_sweep_enabled')}
          />
          Enable Auto-Sweep tracking for this account
        </label>

        {autoSweepEnabled && (
          <div className={styles.previewGrid}>
            <Controller
              name="sweep_out_threshold"
              control={control}
              render={({ field }) => (
                <CurrencyInput
                  label="Sweep-Out Trigger Balance"
                  value={field.value}
                  onChange={field.onChange}
                  currency={currency}
                  error={errors.sweep_out_threshold?.message}
                  helperText="Balance above which funds sweep to FD"
                />
              )}
            />

            <Controller
              name="sweep_retained_balance"
              control={control}
              render={({ field }) => (
                <CurrencyInput
                  label="Minimum Retained Balance"
                  value={field.value}
                  onChange={field.onChange}
                  currency={currency}
                  error={errors.sweep_retained_balance?.message}
                  helperText="Minimum kept in savings"
                />
              )}
            />

            <Controller
              name="sweep_increment"
              control={control}
              render={({ field }) => (
                <CurrencyInput
                  label="Sweep Increment / Multiplier"
                  value={field.value}
                  onChange={field.onChange}
                  currency={currency}
                  error={errors.sweep_increment?.message}
                  helperText="e.g. ₹10,000 blocks"
                />
              )}
            />
          </div>
        )}
      </FormSection>

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add any account details, branch information, or tracking notes..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions
        onBack={onBack}
        submitLabel="Review Account Details"
        isSubmitting={isSubmitting}
      />
    </form>
  );
};
