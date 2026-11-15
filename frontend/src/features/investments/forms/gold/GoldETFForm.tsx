import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  goldEtfSchema,
  GoldEtfFormData,
} from '../../schemas/investmentSchemas';
import {
  FormField,
  CurrencyInput,
  NumberInput,
  DatePicker,
  FormSection,
  FormActions,
} from '@/shared/components/forms';
import styles from '../forms.module.css';

export interface GoldETFFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<GoldEtfFormData>;
  onSubmit: (data: GoldEtfFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const GoldETFForm: React.FC<GoldETFFormProps> = ({
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
  } = useForm<GoldEtfFormData>({
    resolver: zodResolver(goldEtfSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      fund_name: initialValues?.fund_name || '',
      symbol: initialValues?.symbol || '',
      exchange: initialValues?.exchange || 'NSE',
      units: initialValues?.units ?? 10,
      purchase_price: initialValues?.purchase_price ?? 65,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      brokerage_fees: initialValues?.brokerage_fees ?? 0,
      notes: initialValues?.notes || '',
    },
  });

  const units = watch('units') || 0;
  const price = watch('purchase_price') || 0;
  const fees = watch('brokerage_fees') || 0;
  const totalCost = units * price + fees;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="ETF Scheme & Ticker"
        description="Exchange Traded Fund backed by physical bullion."
        columns={2}
      >
        <FormField
          label="ETF Fund Name"
          htmlFor="fund_name"
          required
          error={errors.fund_name?.message}
          helperText="e.g. Nippon India ETF Gold BeES, HDFC Gold ETF"
        >
          <input
            id="fund_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Nippon India ETF Gold BeES"
            {...register('fund_name')}
          />
        </FormField>

        <FormField
          label="Exchange Symbol / Ticker"
          htmlFor="symbol"
          required
          error={errors.symbol?.message}
          helperText="e.g. GOLDBEES, HDFCMFGETF"
        >
          <input
            id="symbol"
            type="text"
            className={styles.textInput}
            placeholder="e.g. GOLDBEES"
            style={{ textTransform: 'uppercase' }}
            {...register('symbol')}
          />
        </FormField>

        <FormField label="Exchange" htmlFor="exchange" required error={errors.exchange?.message}>
          <select id="exchange" className={styles.selectInput} {...register('exchange')}>
            <option value="NSE">NSE (National Stock Exchange)</option>
            <option value="BSE">BSE (Bombay Stock Exchange)</option>
          </select>
        </FormField>

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
        title="Holding & Trade Execution"
        description="Units purchased, price per unit, and brokerage."
        columns={2}
      >
        <Controller
          name="units"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Units"
              value={field.value}
              onChange={field.onChange}
              min={0.001}
              precision={3}
              error={errors.units?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_price"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Purchase Price per Unit"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.purchase_price?.message}
              required
            />
          )}
        />

        <Controller
          name="brokerage_fees"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Brokerage & Taxes"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.brokerage_fees?.message}
              optional
            />
          )}
        />
      </FormSection>

      {/* Summary */}
      {totalCost > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Trade Capital</span>
              <span className={styles.previewItemValue}>
                ₹{totalCost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>{units} ETF units</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Demat account details or broker..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Gold ETF" isSubmitting={isSubmitting} />
    </form>
  );
};
