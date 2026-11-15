import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  sovereignGoldBondSchema,
  SovereignGoldBondFormData,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
  NumberInput,
  PercentageInput,
  DatePicker,
  FormSection,
  FormActions,
} from '@/shared/components/forms';
import styles from '../forms.module.css';

export interface SovereignGoldBondFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<SovereignGoldBondFormData>;
  onSubmit: (data: SovereignGoldBondFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const SovereignGoldBondForm: React.FC<SovereignGoldBondFormProps> = ({
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
  } = useForm<SovereignGoldBondFormData>({
    resolver: zodResolver(sovereignGoldBondSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      series_name: initialValues?.series_name || '',
      units_grams: initialValues?.units_grams ?? 5,
      issue_price_per_gram: initialValues?.issue_price_per_gram ?? 6250,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      coupon_rate_pct: initialValues?.coupon_rate_pct ?? 2.5,
      maturity_date: initialValues?.maturity_date || '',
      notes: initialValues?.notes || '',
    },
  });

  const unitsGrams = watch('units_grams') || 0;
  const issuePrice = watch('issue_price_per_gram') || 0;
  const couponRate = watch('coupon_rate_pct') || 2.5;

  const totalInvested = unitsGrams * issuePrice;
  const annualInterest = (totalInvested * couponRate) / 100;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="SGB Series & Issue Terms"
        description="RBI Sovereign Gold Bond tranche and issue price details."
        columns={2}
      >
        <FormField
          label="SGB Series Tranche"
          htmlFor="series_name"
          required
          error={errors.series_name?.message}
          helperText="e.g. SGB 2023-24 Series IV, SGB 2020-21 Series VI"
        >
          <input
            id="series_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. SGB 2023-24 Series IV"
            {...register('series_name')}
          />
        </FormField>

        <Controller
          name="coupon_rate_pct"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="RBI Annual Interest (Coupon)"
              value={field.value}
              onChange={field.onChange}
              error={errors.coupon_rate_pct?.message}
              helperText="Government sovereign rate (standard 2.50%)"
            />
          )}
        />

        <Controller
          name="purchase_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Issue / Subscription Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.purchase_date?.message}
              required
            />
          )}
        />

        <Controller
          name="maturity_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="SGB 8-Year Maturity Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.maturity_date?.message}
              required
              helperText="Final redemption after 8 years (tax-free capital gains)"
            />
          )}
        />
      </FormSection>

      <FormSection
        title="Holding & Investment Amount"
        description="Units in grams (1 gram = 1 SGB unit) and issue price."
        columns={2}
      >
        <Controller
          name="units_grams"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Gold Grams (SGB Units)"
              value={field.value}
              onChange={field.onChange}
              min={1}
              step={1}
              unit="g"
              error={errors.units_grams?.message}
              required
            />
          )}
        />

        <Controller
          name="issue_price_per_gram"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Issue Price / Unit"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.issue_price_per_gram?.message}
              required
            />
          )}
        />
      </FormSection>

      {/* SGB Benefits Preview */}
      {totalInvested > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>SGB Sovereign Cash Flow & Tax Status</span>
            </div>
            <span className={styles.previewBadge}>Sovereign Guarantee</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Subscription Capital</span>
              <span className={styles.previewItemValue}>
                ₹{totalInvested.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>{unitsGrams} grams pure gold backing</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Annual Interest Received</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-success, #10b981)' }}>
                +₹{annualInterest.toLocaleString('en-IN', { minimumFractionDigits: 2 })} / yr
              </span>
              <span className={styles.previewItemSub}>Paid semi-annually directly to bank</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Capital Gains Tax</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-primary)' }}>
                0% Exempt
              </span>
              <span className={styles.previewItemSub}>Tax-free on redemption after 8 years</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="RBI Holding Certificate number, demat or physical depository..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review SGB Holding" isSubmitting={isSubmitting} />
    </form>
  );
};
