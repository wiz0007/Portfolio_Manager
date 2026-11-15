import React, { useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  physicalGoldSchema,
  PhysicalGoldFormData,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
  NumberInput,
  DatePicker,
  FormSection,
  FormActions,
} from '@/shared/components/forms';
import { calculateGoldPurityWeight } from '../../utils/financialCalculators';
import styles from '../forms.module.css';

export interface PhysicalGoldFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<PhysicalGoldFormData>;
  onSubmit: (data: PhysicalGoldFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const PhysicalGoldForm: React.FC<PhysicalGoldFormProps> = ({
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
  } = useForm<PhysicalGoldFormData>({
    resolver: zodResolver(physicalGoldSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      item_name: initialValues?.item_name || '',
      gold_form: initialValues?.gold_form || 'COIN',
      purity: initialValues?.purity || '24K',
      gross_weight_grams: initialValues?.gross_weight_grams ?? 10,
      making_charges: initialValues?.making_charges ?? 0,
      purchase_price_total: initialValues?.purchase_price_total ?? 75000,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      storage_location: initialValues?.storage_location || 'Bank Locker',
      notes: initialValues?.notes || '',
    },
  });

  const grossWeight = watch('gross_weight_grams') || 0;
  const purity = watch('purity') || '24K';
  const totalPrice = watch('purchase_price_total') || 0;

  // Live pure gold calculation
  const netPureGoldGrams = useMemo(() => {
    return calculateGoldPurityWeight(grossWeight, purity);
  }, [grossWeight, purity]);

  const effectiveRatePerGram = grossWeight > 0 ? totalPrice / grossWeight : 0;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Gold Item & Purity"
        description="Physical gold type, certified hallmark purity, and item description."
        columns={2}
      >
        <FormField
          label="Item Description / Nickname"
          htmlFor="item_name"
          required
          error={errors.item_name?.message}
          helperText="e.g. 10g MMTC 999 Gold Bar, Tanishq Gold Coin"
        >
          <input
            id="item_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. 10g Gold Coin"
            {...register('item_name')}
          />
        </FormField>

        <FormField label="Physical Form" htmlFor="gold_form" required error={errors.gold_form?.message}>
          <select id="gold_form" className={styles.selectInput} {...register('gold_form')}>
            <option value="COIN">Gold Coin</option>
            <option value="BAR">Gold Bar / Bullion</option>
            <option value="JEWELLERY">Hallmarked Jewellery</option>
            <option value="OTHER">Other Physical Gold</option>
          </select>
        </FormField>

        <FormField label="Gold Purity (BIS Hallmark)" htmlFor="purity" required error={errors.purity?.message}>
          <select id="purity" className={styles.selectInput} {...register('purity')}>
            <option value="24K">24 Karat (99.9% Pure Bullion)</option>
            <option value="22K">22 Karat (91.6% Standard Jewellery)</option>
            <option value="18K">18 Karat (75.0% Jewellery)</option>
            <option value="14K">14 Karat (58.5% Jewellery)</option>
          </select>
        </FormField>

        <FormField
          label="Storage Location / Custody"
          htmlFor="storage_location"
          optional
          error={errors.storage_location?.message}
          helperText="e.g. Bank Locker, Home Safe"
        >
          <input
            id="storage_location"
            type="text"
            className={styles.textInput}
            placeholder="e.g. SBI Locker #104"
            {...register('storage_location')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Weight & Acquisition Cost"
        description="Gross grams, making fees, and total purchase bill amount."
        columns={2}
      >
        <Controller
          name="gross_weight_grams"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Gross Weight (Grams)"
              value={field.value}
              onChange={field.onChange}
              min={0.01}
              precision={3}
              unit="g"
              error={errors.gross_weight_grams?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_price_total"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Total Purchase Price Paid"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.purchase_price_total?.message}
              required
            />
          )}
        />

        <Controller
          name="making_charges"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Making Charges & GST (Included)"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.making_charges?.message}
              optional
              helperText="Jeweller fabrication fee"
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

      {/* Pure Gold & Rate Breakdown Preview */}
      {grossWeight > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>Purity Weight & Net Valuation Basis</span>
            </div>
            <span className={styles.previewBadge}>Standard 24K Normalization</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Net 24K Pure Gold Weight</span>
              <span className={styles.previewItemValue} style={{ color: '#eab308' }}>
                {netPureGoldGrams.toFixed(3)} g
              </span>
              <span className={styles.previewItemSub}>Adjusted from {grossWeight}g @ {purity}</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Effective Rate Paid / Gram</span>
              <span className={styles.previewItemValue}>
                ₹{effectiveRatePerGram.toFixed(2)} / g
              </span>
              <span className={styles.previewItemSub}>Gross weight basis</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Invoice / Bill number, BIS Hallmark certificate id, jeweller name..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Gold Holding" isSubmitting={isSubmitting} />
    </form>
  );
};
