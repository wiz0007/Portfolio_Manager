import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  realEstateSchema,
  RealEstateFormData,
  RealEstateInput,
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
import styles from '../forms.module.css';

const STATE_OPTIONS = [
  { value: 'Delhi', label: 'Delhi (NCT)' },
  { value: 'Uttarakhand', label: 'Uttarakhand' },
  { value: 'Maharashtra', label: 'Maharashtra' },
  { value: 'Karnataka', label: 'Karnataka' },
  { value: 'Uttar Pradesh', label: 'Uttar Pradesh' },
  { value: 'Haryana', label: 'Haryana' },
  { value: 'Tamil Nadu', label: 'Tamil Nadu' },
  { value: 'Telangana', label: 'Telangana' },
  { value: 'Gujarat', label: 'Gujarat' },
  { value: 'Other State', label: 'Other State / UT' },
];

export interface RealEstateFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<RealEstateFormData>;
  onSubmit: (data: RealEstateFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const RealEstateForm: React.FC<RealEstateFormProps> = ({
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
  } = useForm<RealEstateInput, any, RealEstateFormData>({
    resolver: zodResolver(realEstateSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      property_name: initialValues?.property_name || '',
      property_type: initialValues?.property_type || 'RESIDENTIAL',
      property_use: initialValues?.property_use || 'SELF_OCCUPIED',
      state: initialValues?.state || 'Delhi',
      city: initialValues?.city || '',
      locality: initialValues?.locality || '',
      address_line: initialValues?.address_line || '',
      built_up_area: initialValues?.built_up_area,
      plot_area: initialValues?.plot_area,
      area_unit: initialValues?.area_unit || 'SQ_FT',
      ownership_percentage: initialValues?.ownership_percentage ?? 100,
      purchase_price: initialValues?.purchase_price ?? 5000000,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      stamp_duty_paid: initialValues?.stamp_duty_paid ?? 0,
      registration_fee_paid: initialValues?.registration_fee_paid ?? 0,
      renovation_expenses: initialValues?.renovation_expenses ?? 0,
      monthly_rental_income: initialValues?.monthly_rental_income ?? 0,
      valuation_method: initialValues?.valuation_method || 'USER_ESTIMATE',
      estimated_current_value: initialValues?.estimated_current_value ?? 5500000,
      notes: initialValues?.notes || '',
    },
  });

  const purchasePrice = watch('purchase_price') || 0;
  const stampDuty = watch('stamp_duty_paid') || 0;
  const regFee = watch('registration_fee_paid') || 0;
  const renovation = watch('renovation_expenses') || 0;
  const ownershipPct = watch('ownership_percentage') || 100;
  const estVal = watch('estimated_current_value') || 0;

  const totalAcquisitionCost = purchasePrice + stampDuty + regFee + renovation;
  const userCostShare = (totalAcquisitionCost * ownershipPct) / 100;
  const userCurrentValue = (estVal * ownershipPct) / 100;
  const unrealizedGain = userCurrentValue - userCostShare;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Property Identification & Use"
        description="Type of property, location, and current occupancy status."
        columns={2}
      >
        <FormField
          label="Property Title / Nickname"
          htmlFor="property_name"
          required
          error={errors.property_name?.message}
          helperText="e.g. 3BHK South Extension, Dehradun Holiday Villa"
        >
          <input
            id="property_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Rohini Residential Flat"
            {...register('property_name')}
          />
        </FormField>

        <FormField label="Property Type" htmlFor="property_type" required error={errors.property_type?.message}>
          <select id="property_type" className={styles.selectInput} {...register('property_type')}>
            <option value="RESIDENTIAL">Residential (Flat / House / Villa)</option>
            <option value="COMMERCIAL">Commercial (Office / Retail / Shop)</option>
            <option value="LAND">Land / Plot / Agricultural</option>
            <option value="INDUSTRIAL">Industrial / Warehouse</option>
          </select>
        </FormField>

        <FormField label="Current Property Use" htmlFor="property_use" required error={errors.property_use?.message}>
          <select id="property_use" className={styles.selectInput} {...register('property_use')}>
            <option value="SELF_OCCUPIED">Self-Occupied (Primary / Secondary Residence)</option>
            <option value="RENTED">Rented Out (Generating Rental Cash Flow)</option>
            <option value="VACANT">Vacant / Idle</option>
            <option value="UNDER_CONSTRUCTION">Under Construction</option>
          </select>
        </FormField>

        <Controller
          name="state"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="State / Union Territory"
              options={STATE_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              error={errors.state?.message}
              required
            />
          )}
        />

        <FormField label="City / District" htmlFor="city" required error={errors.city?.message}>
          <input
            id="city"
            type="text"
            className={styles.textInput}
            placeholder="e.g. New Delhi, Dehradun, Mumbai"
            {...register('city')}
          />
        </FormField>

        <FormField label="Locality / Sector" htmlFor="locality" required error={errors.locality?.message}>
          <input
            id="locality"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Rajpur Road, Vasant Kunj"
            {...register('locality')}
          />
        </FormField>

        <FormField label="Address / Plot Details" htmlFor="address_line" optional error={errors.address_line?.message}>
          <input
            id="address_line"
            type="text"
            className={styles.textInput}
            placeholder="Flat 402, Block C, Tower 1"
            {...register('address_line')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Dimensions & Ownership Share"
        description="Area metrics and percentage ownership in joint title deeds."
        columns={3}
      >
        <Controller
          name="built_up_area"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Built-Up / Carpet Area"
              value={field.value}
              onChange={field.onChange}
              min={1}
              error={errors.built_up_area?.message}
              optional
            />
          )}
        />

        <Controller
          name="plot_area"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Plot / Land Area"
              value={field.value}
              onChange={field.onChange}
              min={1}
              error={errors.plot_area?.message}
              optional
            />
          )}
        />

        <FormField label="Area Measurement Unit" htmlFor="area_unit">
          <select id="area_unit" className={styles.selectInput} {...register('area_unit')}>
            <option value="SQ_FT">Square Feet (Sq. Ft.)</option>
            <option value="SQ_METER">Square Metres (Sq. M.)</option>
            <option value="BIGHA">Bigha (Uttarakhand / UP)</option>
            <option value="ACRE">Acre</option>
          </select>
        </FormField>

        <Controller
          name="ownership_percentage"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="Your Ownership Percentage"
              value={field.value}
              onChange={field.onChange}
              min={1}
              max={100}
              error={errors.ownership_percentage?.message}
              required
              helperText="100% for sole ownership"
            />
          )}
        />
      </FormSection>

      <FormSection
        title="Acquisition Costs & Statutory Fees"
        description="Base agreement value, stamp duty, registration charges, and capital improvements."
        columns={2}
      >
        <Controller
          name="purchase_price"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Agreed Purchase / Sale Consideration"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.purchase_price?.message}
              required
            />
          )}
        />

        <Controller
          name="purchase_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Acquisition / Registration Date"
              value={field.value}
              onChange={field.onChange}
              error={errors.purchase_date?.message}
              required
            />
          )}
        />

        <Controller
          name="stamp_duty_paid"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Stamp Duty Paid"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.stamp_duty_paid?.message}
              optional
              helperText="e.g. 4%-7% depending on state and gender"
            />
          )}
        />

        <Controller
          name="registration_fee_paid"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Registration Fees Paid"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.registration_fee_paid?.message}
              optional
              helperText="Sub-Registrar official fee (usually 1%-2%)"
            />
          )}
        />

        <Controller
          name="renovation_expenses"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Capital Improvement / Interior Outlay"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.renovation_expenses?.message}
              optional
            />
          )}
        />

        <Controller
          name="monthly_rental_income"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Monthly Gross Rental Income"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.monthly_rental_income?.message}
              optional
              helperText="If rented out"
            />
          )}
        />
      </FormSection>

      <FormSection
        title="Current Valuation & Methodology"
        description="Estimated market value and basis of valuation."
        columns={2}
      >
        <Controller
          name="estimated_current_value"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Estimated Current Market Value (100% Asset)"
              value={field.value}
              onChange={field.onChange}
              currency={defaultCurrency}
              error={errors.estimated_current_value?.message}
              required
            />
          )}
        />

        <FormField label="Valuation Basis" htmlFor="valuation_method" error={errors.valuation_method?.message}>
          <select id="valuation_method" className={styles.selectInput} {...register('valuation_method')}>
            <option value="USER_ESTIMATE">User Assessment / Recent Comp Sales</option>
            <option value="GOVERNMENT_REFERENCE">Circle Rate / Jantri Reference</option>
            <option value="APPRAISAL">Independent Chartered Surveyor Appraisal</option>
            <option value="MANUAL">Manual Cost Basis</option>
          </select>
        </FormField>
      </FormSection>

      {/* Real Estate Financial Position Preview */}
      {userCostShare > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>Real Estate Equity & Cost Basis Preview</span>
            </div>
            <span className={styles.previewBadge}>{ownershipPct}% Ownership Share</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total All-In Acquisition Cost</span>
              <span className={styles.previewItemValue}>
                ₹{totalAcquisitionCost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>Purchase + Stamp + Reg + Interiors</span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Your Net Cost Share ({ownershipPct}%)</span>
              <span className={styles.previewItemValue}>
                ₹{userCostShare.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Your Share Estimated Value</span>
              <span className={styles.previewItemValue} style={{ color: 'var(--color-primary)' }}>
                ₹{userCurrentValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Unrealized Capital Gain</span>
              <span
                className={styles.previewItemValue}
                style={{ color: unrealizedGain >= 0 ? 'var(--color-success, #10b981)' : 'var(--color-error)' }}
              >
                {unrealizedGain >= 0 ? '+' : ''}₹{unrealizedGain.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
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
            placeholder="Property registration deed number, Sub-Registrar office, khata / khasra details..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Real Estate Asset" isSubmitting={isSubmitting} />
    </form>
  );
};
