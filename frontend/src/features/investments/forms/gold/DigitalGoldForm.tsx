import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  digitalGoldSchema,
  DigitalGoldFormData,
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

const PROVIDER_OPTIONS = [
  { value: 'MMTC-PAMP', label: 'MMTC-PAMP India' },
  { value: 'SafeGold', label: 'SafeGold (Digital Gold India Pvt Ltd)' },
  { value: 'Augmont', label: 'Augmont Gold' },
  { value: 'Other Provider', label: 'Other Digital Gold Platform' },
];

export interface DigitalGoldFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<DigitalGoldFormData>;
  onSubmit: (data: DigitalGoldFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const DigitalGoldForm: React.FC<DigitalGoldFormProps> = ({
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
  } = useForm<DigitalGoldFormData>({
    resolver: zodResolver(digitalGoldSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      provider: initialValues?.provider || 'MMTC-PAMP',
      weight_grams: initialValues?.weight_grams ?? 5,
      purchase_amount: initialValues?.purchase_amount ?? 37500,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      notes: initialValues?.notes || '',
    },
  });

  const weight = watch('weight_grams') || 0;
  const amount = watch('purchase_amount') || 0;
  const effectiveRate = weight > 0 ? amount / weight : 0;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Vault Custodian & Provider"
        description="Select the 24K digital gold vault custodian."
        columns={2}
      >
        <Controller
          name="provider"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="Digital Gold Custodian"
              options={PROVIDER_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              error={errors.provider?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Purchase Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.purchase_date?.message}
              required
            />
          )}
        />
      </FormSection>

      <FormSection
        title="Purchased Holding"
        description="Weight credited in vault and amount paid."
        columns={2}
      >
        <Controller
          name="weight_grams"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Accumulated Weight (Grams)"
              value={field.value}
              onChange={field.onChange}
              min={0.0001}
              precision={4}
              unit="g"
              error={errors.weight_grams?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_amount"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Total Purchase Amount (inc. 3% GST)"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.purchase_amount?.message}
              required
            />
          )}
        />
      </FormSection>

      {/* Breakdown */}
      {weight > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Effective Price per Gram Paid</span>
              <span className={styles.previewItemValue}>₹{effectiveRate.toFixed(2)} / g</span>
              <span className={styles.previewItemSub}>All-inclusive cost per gram</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="App partner (e.g. Google Pay, Paytm, PhonePe, Jar)..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Digital Gold" isSubmitting={isSubmitting} />
    </form>
  );
};
