import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  agriculturalLandSchema,
  AgriculturalLandFormData,
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
  { value: 'Uttarakhand', label: 'Uttarakhand' },
  { value: 'Delhi', label: 'Delhi (NCT)' },
  { value: 'Uttar Pradesh', label: 'Uttar Pradesh' },
  { value: 'Haryana', label: 'Haryana' },
  { value: 'Punjab', label: 'Punjab' },
  { value: 'Maharashtra', label: 'Maharashtra' },
  { value: 'Karnataka', label: 'Karnataka' },
  { value: 'Rajasthan', label: 'Rajasthan' },
  { value: 'Madhya Pradesh', label: 'Madhya Pradesh' },
  { value: 'Other State', label: 'Other State / UT' },
];

const PROPERTY_TYPE_OPTIONS = [
  { value: 'LAND', label: 'Vacant Land' },
  { value: 'AGRICULTURAL', label: 'Agricultural Land / Farm' },
  { value: 'PLOT', label: 'Residential / Commercial Plot' },
];

const LAND_CLASSIFICATION_OPTIONS = [
  { value: 'AGRICULTURAL', label: 'Agricultural (Krishi)' },
  { value: 'RESIDENTIAL', label: 'Residential (Aawasiya)' },
  { value: 'COMMERCIAL', label: 'Commercial (Vyavasayik)' },
  { value: 'OTHER', label: 'Other / Mixed Use' },
];

const AREA_UNIT_OPTIONS = [
  { value: 'ACRE', label: 'Acres' },
  { value: 'BIGHA', label: 'Bigha' },
  { value: 'SQ_FT', label: 'Sq. Feet' },
  { value: 'SQ_METER', label: 'Sq. Meters' },
];

export interface AgriculturalLandFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<AgriculturalLandFormData>;
  onSubmit: (data: AgriculturalLandFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const AgriculturalLandForm: React.FC<AgriculturalLandFormProps> = ({
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
  } = useForm<AgriculturalLandFormData>({
    resolver: zodResolver(agriculturalLandSchema),
    defaultValues: {
      portfolio_id: portfolioId,
      property_name: initialValues?.property_name || '',
      property_type: initialValues?.property_type || 'AGRICULTURAL',
      land_classification: initialValues?.land_classification || 'AGRICULTURAL',
      country: initialValues?.country || 'India',
      state: initialValues?.state || 'Uttarakhand',
      district: initialValues?.district || '',
      tehsil: initialValues?.tehsil || '',
      locality: initialValues?.locality || '',
      village: initialValues?.village || '',
      survey_or_plot_number: initialValues?.survey_or_plot_number || '',
      land_area: initialValues?.land_area ?? 1,
      area_unit: initialValues?.area_unit || 'ACRE',
      ownership_percentage: initialValues?.ownership_percentage ?? 100,
      acquisition_date: initialValues?.acquisition_date || new Date().toISOString().split('T')[0],
      purchase_price: initialValues?.purchase_price ?? 2500000,
      registration_charges: initialValues?.registration_charges ?? 0,
      stamp_duty: initialValues?.stamp_duty ?? 0,
      other_acquisition_costs: initialValues?.other_acquisition_costs ?? 0,
      estimated_current_value: initialValues?.estimated_current_value ?? 2800000,
      valuation_date: initialValues?.valuation_date || new Date().toISOString().split('T')[0],
      valuation_source: initialValues?.valuation_source || 'Circle Rate / Government Circle Rate',
      expected_annual_appreciation: initialValues?.expected_annual_appreciation ?? 8,
      notes: initialValues?.notes || '',
    },
  });

  const purchasePrice = watch('purchase_price') || 0;
  const stampDuty = watch('stamp_duty') || 0;
  const registrationCharges = watch('registration_charges') || 0;
  const otherCosts = watch('other_acquisition_costs') || 0;
  const ownershipPct = watch('ownership_percentage') || 100;
  const estVal = watch('estimated_current_value') || 0;

  const totalAcquisitionCost = purchasePrice + stampDuty + registrationCharges + otherCosts;
  const userCostShare = (totalAcquisitionCost * ownershipPct) / 100;
  const userCurrentValue = (estVal * ownershipPct) / 100;
  const unrealizedGain = userCurrentValue - userCostShare;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Land & Property Identification"
        description="Specify the plot or agricultural land classification, location, and survey identifiers."
        columns={2}
      >
        <FormField
          id="property_name"
          label="Property / Plot Name"
          optional
          error={errors.property_name?.message}
          helperText="e.g. Dehradun Orchard Land, Haridwar Bypass Plot"
        >
          <input
            id="property_name"
            type="text"
            {...register('property_name')}
            placeholder="e.g. Dehradun Orchard"
            className={styles.textInput}
          />
        </FormField>

        <FormField
          id="property_type"
          label="Property Type"
          required
          error={errors.property_type?.message}
        >
          <select id="property_type" {...register('property_type')} className={styles.selectInput}>
            {PROPERTY_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </FormField>

        <FormField
          id="land_classification"
          label="Land Classification"
          required
          error={errors.land_classification?.message}
        >
          <select
            id="land_classification"
            {...register('land_classification')}
            className={styles.selectInput}
          >
            {LAND_CLASSIFICATION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </FormField>

        <Controller
          name="state"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="State / Union Territory"
              required
              options={STATE_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.state?.message}
            />
          )}
        />

        <FormField
          id="district"
          label="District"
          required
          error={errors.district?.message}
        >
          <input
            id="district"
            type="text"
            {...register('district')}
            placeholder="e.g. Dehradun, Nainital, South West Delhi"
            className={styles.textInput}
          />
        </FormField>

        <FormField
          id="tehsil"
          label="Tehsil / Sub-District"
          optional
          error={errors.tehsil?.message}
        >
          <input
            id="tehsil"
            type="text"
            {...register('tehsil')}
            placeholder="e.g. Vikas Nagar, Rishikesh"
            className={styles.textInput}
          />
        </FormField>

        <FormField
          id="village"
          label="Village / Mouza / Locality"
          optional
          error={errors.village?.message}
        >
          <input
            id="village"
            type="text"
            {...register('village')}
            placeholder="e.g. Sahaspur Village"
            className={styles.textInput}
          />
        </FormField>

        <FormField
          id="survey_or_plot_number"
          label="Khasra / Khatauni / Survey No."
          optional
          error={errors.survey_or_plot_number?.message}
          helperText="Land revenue identification number"
        >
          <input
            id="survey_or_plot_number"
            type="text"
            {...register('survey_or_plot_number')}
            placeholder="e.g. Khasra 142/2, Khata 58"
            className={styles.textInput}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Land Area & Ownership"
        description="Physical dimensions and your proportional ownership share."
        columns={3}
      >
        <Controller
          name="land_area"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Land Area"
              required
              min={0.0001}
              step="any"
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.land_area?.message}
            />
          )}
        />

        <FormField id="area_unit" label="Area Unit" required error={errors.area_unit?.message}>
          <select id="area_unit" {...register('area_unit')} className={styles.selectInput}>
            {AREA_UNIT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </FormField>

        <Controller
          name="ownership_percentage"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="Ownership Share"
              required
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.ownership_percentage?.message}
              helperText="100% for sole ownership"
            />
          )}
        />
      </FormSection>

      <FormSection
        title="Acquisition & Transaction Costs"
        description="Base purchase cost, government stamp duty, registration charges, and transaction fees."
        columns={2}
      >
        <Controller
          name="acquisition_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Acquisition Date"
              required
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.acquisition_date?.message}
            />
          )}
        />

        <Controller
          name="purchase_price"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Agreement / Base Purchase Price"
              required
              currency={defaultCurrency}
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.purchase_price?.message}
            />
          )}
        />

        <Controller
          name="stamp_duty"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Stamp Duty Paid"
              optional
              currency={defaultCurrency}
              value={field.value ?? 0}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.stamp_duty?.message}
            />
          )}
        />

        <Controller
          name="registration_charges"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Registration Charges Paid"
              optional
              currency={defaultCurrency}
              value={field.value ?? 0}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.registration_charges?.message}
            />
          )}
        />

        <Controller
          name="other_acquisition_costs"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Brokerage & Legal Fees"
              optional
              currency={defaultCurrency}
              value={field.value ?? 0}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.other_acquisition_costs?.message}
              helperText="Demarcation, mutation, legal title check, and broker fees"
            />
          )}
        />
      </FormSection>

      <FormSection
        title="Current Valuation & Projections"
        description="Provide the latest estimated market value or circle rate valuation."
        columns={2}
      >
        <Controller
          name="estimated_current_value"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Estimated Current Value"
              optional
              currency={defaultCurrency}
              value={field.value ?? 0}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.estimated_current_value?.message}
            />
          )}
        />

        <Controller
          name="valuation_date"
          control={control}
          render={({ field }) => (
            <DatePicker
              label="Valuation Date"
              optional
              value={field.value || ''}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.valuation_date?.message}
            />
          )}
        />

        <FormField
          id="valuation_source"
          label="Valuation Source / Methodology"
          optional
          error={errors.valuation_source?.message}
          helperText="e.g. Government Circle Rate, Registered Valuer, Local Mandi rate"
        >
          <input
            id="valuation_source"
            type="text"
            {...register('valuation_source')}
            placeholder="e.g. Circle Rate Evaluation"
            className={styles.textInput}
          />
        </FormField>

        <Controller
          name="expected_annual_appreciation"
          control={control}
          render={({ field }) => (
            <PercentageInput
              label="Expected Annual Appreciation"
              optional
              value={field.value ?? 0}
              onChange={field.onChange}
              onBlur={field.onBlur}
              error={errors.expected_annual_appreciation?.message}
              helperText="Used for future net-worth projections"
            />
          )}
        />
      </FormSection>

      {/* Calculation Preview */}
      <div className={styles.previewCard}>
        <div className={styles.previewHeader}>
          <div className={styles.previewTitle}>
            <Calculator className="h-4 w-4 text-theme-primary" />
            <span>Land Acquisition & Cost Summary</span>
          </div>
          <span className={styles.previewSubtitle}>Calculated from entered amounts</span>
        </div>

        <div className={styles.previewGrid}>
          <div className={styles.previewItem}>
            <span className={styles.previewLabel}>Total Acquisition Cost</span>
            <span className={styles.previewValue}>
              {defaultCurrency} {totalAcquisitionCost.toLocaleString('en-IN')}
            </span>
            <span className={styles.previewNote}>Includes purchase, duty, registration & legal</span>
          </div>

          <div className={styles.previewItem}>
            <span className={styles.previewLabel}>Your Cost Share ({ownershipPct}%)</span>
            <span className={styles.previewValue}>
              {defaultCurrency} {Math.round(userCostShare).toLocaleString('en-IN')}
            </span>
            <span className={styles.previewNote}>Actual capital outlay</span>
          </div>

          <div className={styles.previewItem}>
            <span className={styles.previewLabel}>Your Current Value Share</span>
            <span className={styles.previewValue}>
              {defaultCurrency} {Math.round(userCurrentValue).toLocaleString('en-IN')}
            </span>
            <span className={styles.previewNote}>Valuation adjusted for ownership</span>
          </div>

          <div className={styles.previewItem}>
            <span className={styles.previewLabel}>Unrealized Value Change</span>
            <span
              className={`${styles.previewValue} ${
                unrealizedGain >= 0 ? styles.positiveText : styles.negativeText
              }`}
            >
              {unrealizedGain >= 0 ? '+' : ''}
              {defaultCurrency} {Math.round(unrealizedGain).toLocaleString('en-IN')}
            </span>
            <span className={styles.previewNote}>
              {userCostShare > 0
                ? `${((unrealizedGain / userCostShare) * 100).toFixed(2)}% net change`
                : 'No cost base'}
            </span>
          </div>
        </div>
      </div>

      <FormSection title="Additional Notes" description="Survey notes, boundaries, or special conditions.">
        <FormField id="notes" label="Notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            rows={3}
            {...register('notes')}
            placeholder="Add any notes regarding boundary demarcation, road access, tubewell rights, or patwari records..."
            className={styles.textareaInput}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} isSubmitting={isSubmitting} submitLabel="Review Land Details" />
    </form>
  );
};
