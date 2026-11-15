import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  bondSchema,
  BondFormData,
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

export interface BondFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<BondFormData>;
  onSubmit: (data: BondFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const BondForm: React.FC<BondFormProps> = ({
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
  } = useForm<BondFormData>({
    resolver: zodResolver(bondSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      issuer_name: initialValues?.issuer_name || '',
      bond_name: initialValues?.bond_name || '',
      isin: initialValues?.isin || '',
      face_value: initialValues?.face_value ?? 1000,
      quantity: initialValues?.quantity ?? 10,
      purchase_price_per_unit: initialValues?.purchase_price_per_unit ?? 1000,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      coupon_rate_pct: initialValues?.coupon_rate_pct ?? 8.5,
      coupon_frequency: initialValues?.coupon_frequency || 'ANNUALLY',
      maturity_date: initialValues?.maturity_date || '',
      credit_rating: initialValues?.credit_rating || 'AAA',
      notes: initialValues?.notes || '',
    },
  });

  const faceValue = watch('face_value') || 0;
  const quantity = watch('quantity') || 0;
  const purchasePrice = watch('purchase_price_per_unit') || 0;
  const couponRate = watch('coupon_rate_pct') || 0;
  const totalInvestment = quantity * purchasePrice;
  const annualCouponIncome = (quantity * faceValue * couponRate) / 100;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Bond Issuer & Identity"
        description="Company, PSU, or Government entity issuing the debt paper."
        columns={2}
      >
        <FormField
          label="Issuer Name"
          htmlFor="issuer_name"
          required
          error={errors.issuer_name?.message}
          helperText="e.g. NHAI, PFC, L&T Finance, RBI"
        >
          <input
            id="issuer_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. REC Limited"
            {...register('issuer_name')}
          />
        </FormField>

        <FormField
          label="Bond Title / Series"
          htmlFor="bond_name"
          required
          error={errors.bond_name?.message}
          helperText="e.g. REC 8.25% 2030 NCD Series II"
        >
          <input
            id="bond_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. 8.25% NCD Series B"
            {...register('bond_name')}
          />
        </FormField>

        <FormField
          label="ISIN Number"
          htmlFor="isin"
          optional
          error={errors.isin?.message}
          helperText="12-character alphanumeric code (e.g. INE020B08781)"
        >
          <input
            id="isin"
            type="text"
            className={styles.textInput}
            placeholder="e.g. INE020B08781"
            maxLength={12}
            {...register('isin')}
          />
        </FormField>

        <FormField
          label="Credit Rating"
          htmlFor="credit_rating"
          optional
          error={errors.credit_rating?.message}
          helperText="e.g. CRISIL AAA, ICRA AA+"
        >
          <input
            id="credit_rating"
            type="text"
            className={styles.textInput}
            placeholder="e.g. CRISIL AAA"
            {...register('credit_rating')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Holding & Valuation Details"
        description="Quantity, face value, acquisition cost, and coupon cash flows."
        columns={2}
      >
        <Controller
          name="quantity"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Quantity (Units)"
              value={field.value}
              onChange={field.onChange}
              min={1}
              step={1}
              error={errors.quantity?.message}
              required
            />
          )}
        />

        <Controller
          name="face_value"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Face Value per Bond"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.face_value?.message}
              required
              helperText="Usually ₹1,000 or ₹10,000 in India"
            />
          )}
        />

        <Controller
          name="purchase_price_per_unit"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Purchase Price per Bond"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.purchase_price_per_unit?.message}
              required
            />
          )}
        />

        <Controller
          name="coupon_rate_pct"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="Annual Coupon Rate"
              value={field.value}
              onChange={field.onChange}
              error={errors.coupon_rate_pct?.message}
              required
            />
          )}
        />

        <FormField
          label="Coupon Payout Frequency"
          htmlFor="coupon_frequency"
          error={errors.coupon_frequency?.message}
        >
          <select id="coupon_frequency" className={styles.selectInput} {...register('coupon_frequency')}>
            <option value="ANNUALLY">Annually</option>
            <option value="SEMI_ANNUALLY">Semi-Annually (Half Yearly)</option>
            <option value="QUARTERLY">Quarterly</option>
            <option value="MONTHLY">Monthly</option>
            <option value="CUMULATIVE">Cumulative (Compounded to Maturity)</option>
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

        <Controller
          name="maturity_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Contractual Maturity Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.maturity_date?.message}
              required
            />
          )}
        />
      </FormSection>

      {/* Cash Flow Summary */}
      {totalInvestment > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <span className={styles.previewTitle}>Bond Cash Flow Preview</span>
            <span className={styles.previewBadge}>Fixed Income Income Projection</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Capital Invested</span>
              <span className={styles.previewItemValue}>
                ₹{totalInvestment.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Annual Coupon Cash Flow</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-success, #10b981)' }}>
                +₹{annualCouponIncome.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Gross annual interest distribution</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Face Value at Redemption</span>
              <span className={styles.previewItemValue}>
                ₹{(quantity * faceValue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Demat holding account, depository participant (NSDL/CDSL)..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Bond" isSubmitting={isSubmitting} />
    </form>
  );
};
