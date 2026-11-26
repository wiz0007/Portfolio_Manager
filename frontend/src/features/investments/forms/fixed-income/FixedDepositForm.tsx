import React, { useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  fixedDepositSchema,
  FixedDepositFormData,
  FixedDepositInput,
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
import { calculateFdMaturity } from '../../utils/financialCalculators';
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
  { value: 'Bajaj Finance', label: 'Bajaj Finance (NBFC)' },
  { value: 'Shriram Finance', label: 'Shriram Finance (NBFC)' },
  { value: 'Other Institution', label: 'Other Bank / NBFC' },
];

export interface FixedDepositFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<FixedDepositFormData>;
  onSubmit: (data: FixedDepositFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const FixedDepositForm: React.FC<FixedDepositFormProps> = ({
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
  } = useForm<FixedDepositInput, any, FixedDepositFormData>({
    resolver: zodResolver(fixedDepositSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      currency: (initialValues?.currency || defaultCurrency) as any,
      bank_name: initialValues?.bank_name || '',
      deposit_nickname: initialValues?.deposit_nickname || '',
      principal_amount: initialValues?.principal_amount ?? 100000,
      start_date: initialValues?.start_date || new Date().toISOString().split('T')[0],
      tenure_value: initialValues?.tenure_value ?? 1,
      tenure_unit: initialValues?.tenure_unit || 'years',
      maturity_date: initialValues?.maturity_date || '',
      annual_rate_pct: initialValues?.annual_rate_pct ?? 7.1,
      compounding_frequency: initialValues?.compounding_frequency || 'quarterly',
      payout_type: initialValues?.payout_type || 'cumulative',
      is_senior_citizen: initialValues?.is_senior_citizen ?? false,
      is_tax_saver: initialValues?.is_tax_saver ?? false,
      auto_renewal: initialValues?.auto_renewal ?? false,
      notes: initialValues?.notes || '',
    },
  });

  const principal = watch('principal_amount');
  const annualRate = watch('annual_rate_pct');
  const tenureVal = watch('tenure_value');
  const tenureUnit = watch('tenure_unit');
  const compoundingFreq = watch('compounding_frequency');
  const payoutType = watch('payout_type');
  const currency = watch('currency') || 'INR';

  // Live calculation preview
  const fdPreview = useMemo(() => {
    return calculateFdMaturity({
      principal: principal || 0,
      annualRatePct: annualRate || 0,
      tenureValue: tenureVal || 0,
      tenureUnit: tenureUnit || 'years',
      compoundingFrequency: compoundingFreq,
      payoutType: payoutType,
    });
  }, [principal, annualRate, tenureVal, tenureUnit, compoundingFreq, payoutType]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Deposit Identity"
        description="Select the issuing bank or financial institution."
        columns={2}
      >
        <Controller
          name="bank_name"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="Bank / NBFC Issuer"
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
          helperText="e.g. SBI 400 Days Amrit Kalash, HDFC 1-Year FD"
        >
          <input
            id="deposit_nickname"
            type="text"
            className={styles.textInput}
            placeholder="e.g. 1 Year Tax Saver FD"
            {...register('deposit_nickname')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Financial & Contractual Terms"
        description="Principal, rate, tenure, and compounding schedule."
        columns={2}
      >
        <Controller
          name="principal_amount"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Principal Deposit Amount"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.principal_amount?.message}
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
              helperText="e.g. 7.10% (Bank contractual rate)"
            />
          )}
        />

        <Controller
          name="start_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Deposit Start Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.start_date?.message}
              required
            />
          )}
        />

        <Controller
          name="maturity_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Maturity Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.maturity_date?.message}
              required
            />
          )}
        />

        <Controller
          name="tenure_value"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Tenure Length"
              value={field.value}
              onChange={field.onChange}
              min={1}
              error={errors.tenure_value?.message}
              required
            />
          )}
        />

        <FormField label="Tenure Unit" htmlFor="tenure_unit" required error={errors.tenure_unit?.message}>
          <select id="tenure_unit" className={styles.selectInput} {...register('tenure_unit')}>
            <option value="days">Days</option>
            <option value="months">Months</option>
            <option value="years">Years</option>
          </select>
        </FormField>

        <FormField
          label="Compounding Frequency"
          htmlFor="compounding_frequency"
          error={errors.compounding_frequency?.message}
        >
          <select
            id="compounding_frequency"
            className={styles.selectInput}
            {...register('compounding_frequency')}
          >
            <option value="quarterly">Quarterly Compounding (Indian Standard)</option>
            <option value="monthly">Monthly Compounding</option>
            <option value="half_yearly">Half Yearly Compounding</option>
            <option value="annually">Annual Compounding</option>
            <option value="simple">Simple Interest (No Compounding)</option>
          </select>
        </FormField>

        <FormField label="Payout Type" htmlFor="payout_type" error={errors.payout_type?.message}>
          <select id="payout_type" className={styles.selectInput} {...register('payout_type')}>
            <option value="cumulative">Cumulative (At Maturity)</option>
            <option value="monthly_payout">Monthly Interest Payout</option>
            <option value="quarterly_payout">Quarterly Interest Payout</option>
          </select>
        </FormField>
      </FormSection>

      {/* Live Calculation Preview Card */}
      {fdPreview.maturityAmount > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>Contractual Yield & Maturity Projection</span>
            </div>
            <span className={styles.previewBadge}>Live Client-Side Preview</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Estimated Maturity Value</span>
              <span className={styles.previewItemValue}>
                ₹{fdPreview.maturityAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Principal + Accumulated Compounded Return</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Interest Earned</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-success, #10b981)' }}>
                +₹{fdPreview.totalInterestEarned.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Over full deposit tenure</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Effective Annualized Yield</span>
              <span className={styles.previewItemValue}>{fdPreview.effectiveAnnualYieldPct}%</span>
              <span className={styles.previewItemSub}>Compound APY equivalent</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Special Flags & Options" columns={3}>
        <label className={styles.checkboxLabel}>
          <input type="checkbox" className={styles.checkboxInput} {...register('is_senior_citizen')} />
          Senior Citizen Scheme
        </label>
        <label className={styles.checkboxLabel}>
          <input type="checkbox" className={styles.checkboxInput} {...register('is_tax_saver')} />
          Tax Saver (5-Yr 80C Lock-in)
        </label>
        <label className={styles.checkboxLabel}>
          <input type="checkbox" className={styles.checkboxInput} {...register('auto_renewal')} />
          Auto-Renewal on Maturity
        </label>
      </FormSection>

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add FDR certificate number, branch details, or nominee info..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Fixed Deposit" isSubmitting={isSubmitting} />
    </form>
  );
};
