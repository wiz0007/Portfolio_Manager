import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  stockSchema,
  StockFormData,
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

export interface StockFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<StockFormData>;
  onSubmit: (data: StockFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const StockForm: React.FC<StockFormProps> = ({
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
  } = useForm<StockFormData>({
    resolver: zodResolver(stockSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      company_name: initialValues?.company_name || '',
      symbol: initialValues?.symbol || '',
      exchange: initialValues?.exchange || 'NSE',
      currency: (initialValues?.currency || defaultCurrency) as any,
      isin: initialValues?.isin || '',
      quantity: initialValues?.quantity ?? 10,
      purchase_price_per_share: initialValues?.purchase_price_per_share ?? 1000,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      brokerage_fees: initialValues?.brokerage_fees ?? 0,
      taxes: initialValues?.taxes ?? 0,
      notes: initialValues?.notes || '',
    },
  });

  const quantity = watch('quantity') || 0;
  const price = watch('purchase_price_per_share') || 0;
  const brokerage = watch('brokerage_fees') || 0;
  const taxes = watch('taxes') || 0;
  const currency = watch('currency') || 'INR';

  const grossCost = quantity * price;
  const totalCost = grossCost + brokerage + taxes;
  const effectiveCostPerShare = quantity > 0 ? totalCost / quantity : 0;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Stock Identification"
        description="Company details, ticker symbol, and exchange."
        columns={2}
      >
        <FormField
          label="Company Name"
          htmlFor="company_name"
          required
          error={errors.company_name?.message}
          helperText="e.g. Reliance Industries Limited"
        >
          <input
            id="company_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Infosys Ltd"
            {...register('company_name')}
          />
        </FormField>

        <FormField
          label="Ticker Symbol"
          htmlFor="symbol"
          required
          error={errors.symbol?.message}
          helperText="Uppercase stock ticker (e.g. INFY, RELIANCE, TCS)"
        >
          <input
            id="symbol"
            type="text"
            className={styles.textInput}
            placeholder="e.g. INFY"
            style={{ textTransform: 'uppercase' }}
            {...register('symbol')}
          />
        </FormField>

        <FormField label="Exchange" htmlFor="exchange" required error={errors.exchange?.message}>
          <select id="exchange" className={styles.selectInput} {...register('exchange')}>
            <option value="NSE">NSE (National Stock Exchange)</option>
            <option value="BSE">BSE (Bombay Stock Exchange)</option>
            <option value="NASDAQ">NASDAQ (US)</option>
            <option value="NYSE">NYSE (US)</option>
            <option value="LSE">LSE (London Stock Exchange)</option>
            <option value="OTHER">Other Exchange</option>
          </select>
        </FormField>

        <FormField
          label="ISIN Number"
          htmlFor="isin"
          optional
          error={errors.isin?.message}
          helperText="12-character security identifier"
        >
          <input
            id="isin"
            type="text"
            className={styles.textInput}
            placeholder="e.g. INE009A01021"
            maxLength={12}
            {...register('isin')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Trade Execution Details"
        description="Share quantity, purchase price, brokerage, and transaction costs."
        columns={2}
      >
        <Controller
          name="quantity"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Quantity (Shares)"
              value={field.value}
              onChange={field.onChange}
              min={0.0001}
              precision={4}
              error={errors.quantity?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_price_per_share"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Purchase Price per Share"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.purchase_price_per_share?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Trade / Execution Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.purchase_date?.message}
              required
            />
          )}
        />

        <Controller
          name="brokerage_fees"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Brokerage Commission"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.brokerage_fees?.message}
              optional
              helperText="e.g. Zerodha / Groww fee (₹20)"
            />
          )}
        />

        <Controller
          name="taxes"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="STT, GST & Stamp Duty"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.taxes?.message}
              optional
              helperText="Statutory transaction taxes"
            />
          )}
        />
      </FormSection>

      {/* Cost Basis Preview */}
      {totalCost > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>Acquisition Cost Basis & Breakeven</span>
            </div>
            <span className={styles.previewBadge}>Effective Cost Breakdown</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Gross Trade Value</span>
              <span className={styles.previewItemValue}>
                ₹{grossCost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>{quantity} shares @ ₹{price}</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Cost (All Inclusive)</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-primary)' }}>
                ₹{totalCost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Includes ₹{(brokerage + taxes).toFixed(2)} fees & taxes</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Net Breakeven Price / Share</span>
              <span className={styles.previewItemValue}>
                ₹{effectiveCostPerShare.toFixed(2)}
              </span>
              <span className={styles.previewItemSub}>Effective acquisition price</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add trade thesis, demat broker (Zerodha, Groww, AngelOne), order ID..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Stock Holding" isSubmitting={isSubmitting} />
    </form>
  );
};
