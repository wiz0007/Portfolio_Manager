import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  mutualFundSchema,
  MutualFundFormData,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
  NumberInput,
  DatePicker,
  SearchSelect,
  FormSection,
  FormActions,
} from '@/shared/components/forms';
import styles from '../forms.module.css';

const AMC_OPTIONS = [
  { value: 'Parag Parikh Financial Advisory Services', label: 'PPFAS Mutual Fund' },
  { value: 'Mirae Asset Mutual Fund', label: 'Mirae Asset Mutual Fund' },
  { value: 'SBI Mutual Fund', label: 'SBI Mutual Fund' },
  { value: 'HDFC Mutual Fund', label: 'HDFC Mutual Fund' },
  { value: 'ICICI Prudential Mutual Fund', label: 'ICICI Prudential Mutual Fund' },
  { value: 'Quant Mutual Fund', label: 'Quant Mutual Fund' },
  { value: 'Nippon India Mutual Fund', label: 'Nippon India Mutual Fund' },
  { value: 'Kotak Mahindra Mutual Fund', label: 'Kotak Mahindra Mutual Fund' },
  { value: 'Axis Mutual Fund', label: 'Axis Mutual Fund' },
  { value: 'Tata Mutual Fund', label: 'Tata Mutual Fund' },
  { value: 'UTI Mutual Fund', label: 'UTI Mutual Fund' },
  { value: 'Other AMC', label: 'Other Asset Management Company' },
];

const CATEGORY_OPTIONS = [
  { value: 'Flexi Cap Fund', label: 'Equity: Flexi Cap Fund' },
  { value: 'Large Cap Fund', label: 'Equity: Large Cap Fund' },
  { value: 'Mid Cap Fund', label: 'Equity: Mid Cap Fund' },
  { value: 'Small Cap Fund', label: 'Equity: Small Cap Fund' },
  { value: 'ELSS Tax Saver', label: 'Equity: ELSS Tax Saver (3-Yr Lock-in)' },
  { value: 'Index Fund', label: 'Equity: Index Fund (Nifty 50 / Next 50)' },
  { value: 'Liquid / Overnight Fund', label: 'Debt: Liquid / Overnight Fund' },
  { value: 'Aggressive Hybrid Fund', label: 'Hybrid: Aggressive Hybrid Fund' },
  { value: 'Arbitrage Fund', label: 'Hybrid: Arbitrage Fund' },
];

export interface MutualFundFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<MutualFundFormData>;
  onSubmit: (data: MutualFundFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const MutualFundForm: React.FC<MutualFundFormProps> = ({
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
  } = useForm<MutualFundFormData>({
    resolver: zodResolver(mutualFundSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      amc_name: initialValues?.amc_name || '',
      scheme_name: initialValues?.scheme_name || '',
      scheme_category: initialValues?.scheme_category || 'Flexi Cap Fund',
      plan: initialValues?.plan || 'DIRECT',
      option: initialValues?.option || 'GROWTH',
      currency: (initialValues?.currency || defaultCurrency) as any,
      units: initialValues?.units ?? 100,
      purchase_nav: initialValues?.purchase_nav ?? 50,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      is_sip: initialValues?.is_sip ?? false,
      sip_amount: initialValues?.sip_amount,
      sip_frequency: initialValues?.sip_frequency || 'MONTHLY',
      notes: initialValues?.notes || '',
    },
  });

  const units = watch('units') || 0;
  const nav = watch('purchase_nav') || 0;
  const isSip = watch('is_sip');
  const currency = watch('currency') || 'INR';
  const totalInvested = units * nav;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Scheme & Fund House"
        description="Select the AMC, scheme name, plan type, and distribution option."
        columns={2}
      >
        <Controller
          name="amc_name"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="Fund House (AMC)"
              options={AMC_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              error={errors.amc_name?.message}
              required
              placeholder="Search or enter AMC..."
            />
          )}
        />

        <FormField
          label="Scheme Name"
          htmlFor="scheme_name"
          required
          error={errors.scheme_name?.message}
          helperText="e.g. Parag Parikh Flexi Cap Fund"
        >
          <input
            id="scheme_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Parag Parikh Flexi Cap Fund"
            {...register('scheme_name')}
          />
        </FormField>

        <Controller
          name="scheme_category"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="SEBI Category"
              options={CATEGORY_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              error={errors.scheme_category?.message}
              required
            />
          )}
        />

        <FormField label="Plan Type" htmlFor="plan" required error={errors.plan?.message}>
          <select id="plan" className={styles.selectInput} {...register('plan')}>
            <option value="DIRECT">Direct Plan (Zero Commission)</option>
            <option value="REGULAR">Regular Plan (Distributor / Broker)</option>
          </select>
        </FormField>

        <FormField label="Option" htmlFor="option" required error={errors.option?.message}>
          <select id="option" className={styles.selectInput} {...register('option')}>
            <option value="GROWTH">Growth (Compounded NAV)</option>
            <option value="IDCW_PAYOUT">IDCW Payout (Dividend Paid Out)</option>
            <option value="IDCW_REINVESTMENT">IDCW Reinvestment</option>
          </select>
        </FormField>
      </FormSection>

      <FormSection
        title="Units & NAV Details"
        description="Allotted mutual fund units and acquisition Net Asset Value."
        columns={2}
      >
        <Controller
          name="units"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Allotted Units"
              value={field.value}
              onChange={field.onChange}
              min={0.001}
              precision={3}
              error={errors.units?.message}
              required
              helperText="Exact units up to 3 decimal places"
            />
          )}
        />

        <Controller
          name="purchase_nav"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Purchase NAV (per unit)"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.purchase_nav?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Allotment / Purchase Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.purchase_date?.message}
              required
            />
          )}
        />
      </FormSection>

      {/* Total Invested Capital Preview */}
      {totalInvested > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>Investment Outflow Preview</span>
            </div>
            <span className={styles.previewBadge}>Initial Cost Basis</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Capital Invested</span>
              <span className={styles.previewItemValue}>
                ₹{totalInvested.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>{units} units @ NAV ₹{nav}</span>
            </div>
          </div>
        </div>
      )}

      <FormSection
        title="SIP Recurring Schedule (Optional)"
        description="Track ongoing Systematic Investment Plan debits."
        columns={2}
      >
        <label className={styles.checkboxLabel} style={{ gridColumn: 'span 2' }}>
          <input type="checkbox" className={styles.checkboxInput} {...register('is_sip')} />
          This holding is linked to an active Systematic Investment Plan (SIP)
        </label>

        {isSip && (
          <>
            <Controller
              name="sip_amount"
              control={control}
              render={({ field }) => (
                <CurrencyInput
                  label="Recurring SIP Amount"
                  value={field.value}
                  onChange={field.onChange}
                  currency={currency}
                  error={errors.sip_amount?.message}
                  helperText="e.g. ₹5,000 / month"
                />
              )}
            />

            <FormField label="SIP Frequency" htmlFor="sip_frequency">
              <select id="sip_frequency" className={styles.selectInput} {...register('sip_frequency')}>
                <option value="MONTHLY">Monthly</option>
                <option value="WEEKLY">Weekly</option>
                <option value="QUARTERLY">Quarterly</option>
              </select>
            </FormField>
          </>
        )}
      </FormSection>

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add folio number, nominee, or platform notes (Kuvera, MF Central, Groww)..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Mutual Fund" isSubmitting={isSubmitting} />
    </form>
  );
};
