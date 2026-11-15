import React, { useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  recurringDepositSchema,
  RecurringDepositFormData,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
  NumberInput,
  PercentageInput,
  DatePicker,
  SearchSelect,
  FormSection,
  FormActions,
} from '@/shared/components/forms';
import { calculateRdMaturity } from '../../utils/financialCalculators';
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
  { value: 'Post Office RD', label: 'India Post Office RD' },
  { value: 'Other Institution', label: 'Other Bank' },
];

export interface RecurringDepositFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<RecurringDepositFormData>;
  onSubmit: (data: RecurringDepositFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const RecurringDepositForm: React.FC<RecurringDepositFormProps> = ({
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
  } = useForm<RecurringDepositFormData>({
    resolver: zodResolver(recurringDepositSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      currency: (initialValues?.currency || defaultCurrency) as any,
      bank_name: initialValues?.bank_name || '',
      deposit_nickname: initialValues?.deposit_nickname || '',
      monthly_installment: initialValues?.monthly_installment ?? 5000,
      start_date: initialValues?.start_date || new Date().toISOString().split('T')[0],
      tenure_months: initialValues?.tenure_months ?? 12,
      annual_rate_pct: initialValues?.annual_rate_pct ?? 6.8,
      installment_due_day: initialValues?.installment_due_day ?? 5,
      notes: initialValues?.notes || '',
    },
  });

  const installment = watch('monthly_installment');
  const annualRate = watch('annual_rate_pct');
  const tenureMonths = watch('tenure_months');
  const currency = watch('currency') || 'INR';

  // Live calculation preview
  const rdPreview = useMemo(() => {
    return calculateRdMaturity({
      monthlyInstallment: installment || 0,
      annualRatePct: annualRate || 0,
      tenureMonths: tenureMonths || 0,
    });
  }, [installment, annualRate, tenureMonths]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="RD Institution & Identity"
        description="Bank or post office where the recurring deposit is opened."
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
              placeholder="Search or enter institution..."
            />
          )}
        />

        <FormField
          label="Deposit Nickname"
          htmlFor="deposit_nickname"
          required
          error={errors.deposit_nickname?.message}
          helperText="e.g. Vacation Fund RD, Monthly Goal"
        >
          <input
            id="deposit_nickname"
            type="text"
            className={styles.textInput}
            placeholder="e.g. SBI 12-Month RD"
            {...register('deposit_nickname')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Installment & Maturity Terms"
        description="Monthly contribution, interest rate, and tenure duration."
        columns={2}
      >
        <Controller
          name="monthly_installment"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Monthly Installment Amount"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.monthly_installment?.message}
              required
            />
          )}
        />

        <Controller
          name="annual_rate_pct"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="Annual Interest Rate"
              value={field.value}
              onChange={field.onChange}
              error={errors.annual_rate_pct?.message}
              required
              helperText="Quarterly compounding applies"
            />
          )}
        />

        <Controller
          name="start_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="First Installment / Start Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.start_date?.message}
              required
            />
          )}
        />

        <Controller
          name="tenure_months"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Tenure (in Months)"
              value={field.value}
              onChange={field.onChange}
              min={6}
              max={120}
              step={1}
              error={errors.tenure_months?.message}
              required
              helperText="Standard range: 6 to 120 months"
            />
          )}
        />

        <Controller
          name="installment_due_day"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Monthly Debit Day of Month"
              value={field.value}
              onChange={field.onChange}
              min={1}
              max={31}
              step={1}
              error={errors.installment_due_day?.message}
              helperText="Day on which installment is debited (1 - 31)"
            />
          )}
        />
      </FormSection>

      {/* Live Calculation Preview Card */}
      {rdPreview.maturityAmount > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>RD Schedule & Maturity Projection</span>
            </div>
            <span className={styles.previewBadge}>Quarterly Compound Preview</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Deposited Amount</span>
              <span className={styles.previewItemValue}>
                ₹{rdPreview.totalDeposited.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Over {tenureMonths} monthly installments</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Estimated Maturity Amount</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-success, #10b981)' }}>
                ₹{rdPreview.maturityAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>At contractual maturity</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Compounded Interest</span>
              <span className={styles.previewItemValue}>
                +₹{rdPreview.totalInterestEarned.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Net accumulated interest</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add account notes, auto-debit bank, or nominee..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Recurring Deposit" isSubmitting={isSubmitting} />
    </form>
  );
};
