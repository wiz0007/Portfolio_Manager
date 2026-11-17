import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  currentAccountSchema,
  CurrentAccountFormData,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
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
  { value: 'Other Bank', label: 'Other Bank / Financial Institution' },
];

export interface CurrentAccountFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<CurrentAccountFormData>;
  onSubmit: (data: CurrentAccountFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const CurrentAccountForm: React.FC<CurrentAccountFormProps> = ({
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
  } = useForm<CurrentAccountFormData>({
    resolver: zodResolver(currentAccountSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      account_type: 'CURRENT',
      currency: (initialValues?.currency || defaultCurrency) as any,
      bank_name: initialValues?.bank_name || '',
      account_nickname: initialValues?.account_nickname || '',
      masked_account_number: initialValues?.masked_account_number || '',
      current_balance: initialValues?.current_balance ?? 0,
      balance_date: initialValues?.balance_date || new Date().toISOString().split('T')[0],
      overdraft_limit: initialValues?.overdraft_limit ?? 0,
      notes: initialValues?.notes || '',
    },
  });

  const currency = watch('currency') || 'INR';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Current Account Information"
        description="Business or operational transactional account details."
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
          helperText="e.g. Business Checking, Operational Pool"
        >
          <input
            id="account_nickname"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Current A/C"
            {...register('account_nickname')}
          />
        </FormField>

        <FormField
          label="Last 4 Digits / Masked A/C"
          htmlFor="masked_account_number"
          optional
          error={errors.masked_account_number?.message}
        >
          <input
            id="masked_account_number"
            type="text"
            className={styles.textInput}
            placeholder="e.g. XX5678"
            maxLength={10}
            {...register('masked_account_number')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Balance & Liquidity"
        description="Available balance and sanctioned overdraft credit lines."
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
          name="overdraft_limit"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Sanctioned Overdraft (OD) Limit"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.overdraft_limit?.message}
              optional
              helperText="Set 0 if no overdraft facility is linked"
            />
          )}
        />
      </FormSection>

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add operational notes or business account purpose..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions
        onBack={onBack}
        submitLabel="Review Current Account"
        isSubmitting={isSubmitting}
      />
    </form>
  );
};
