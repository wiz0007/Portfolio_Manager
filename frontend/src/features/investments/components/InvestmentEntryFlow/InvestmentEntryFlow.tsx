import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, ChevronRight, Check } from 'lucide-react';
import { Portfolio } from '@/features/portfolios/types';
import { AssetCategoryConfig, AssetTypeConfig } from '../../types/investmentTypes';
import { ASSET_CATEGORIES } from '../../config/assetCategories';
import { PortfolioSelector } from '../PortfolioSelector/PortfolioSelector';
import { AssetCategorySelector } from '../AssetCategorySelector/AssetCategorySelector';
import { AssetTypeSelector } from '../AssetTypeSelector/AssetTypeSelector';
import { InvestmentReview } from '../InvestmentReview/InvestmentReview';
import { Button } from '@/shared/ui/Button';
import { useCreateInvestment } from '../../hooks/useInvestments';

// Forms
import {
  SavingsAccountForm,
  CurrentAccountForm,
  FixedDepositForm,
  RecurringDepositForm,
  BondForm,
  StockForm,
  MutualFundForm,
  PhysicalGoldForm,
  DigitalGoldForm,
  GoldETFForm,
  SovereignGoldBondForm,
  RealEstateForm,
  AgriculturalLandForm,
  CryptocurrencyForm,
} from '../../forms';

import styles from './InvestmentEntryFlow.module.css';

export type FlowStep = 'portfolio' | 'category' | 'type' | 'form' | 'review' | 'success';

export interface InvestmentEntryFlowProps {
  portfolios: Portfolio[];
  initialPortfolioId?: string;
  initialCategoryId?: string;
  initialTypeId?: string;
  initialInstrumentId?: string;
  initialSymbol?: string;
  initialName?: string;
  onNavigateStep?: (params: { portfolioId?: string; category?: string; type?: string }) => void;
  isLoadingPortfolios?: boolean;
}

export const InvestmentEntryFlow: React.FC<InvestmentEntryFlowProps> = ({
  portfolios,
  initialPortfolioId,
  initialCategoryId,
  initialTypeId,
  initialInstrumentId,
  initialSymbol,
  initialName,
  onNavigateStep,
  isLoadingPortfolios = false,
}) => {
  const navigate = useNavigate();

  // Find preselected portfolio if passed
  const initialPortfolio =
    portfolios.find((p) => p.id === initialPortfolioId) ||
    (portfolios.length === 1 ? portfolios[0] : null);

  // Find preselected category or look up from initialTypeId
  let initialCategory: AssetCategoryConfig | null = null;
  let initialType: AssetTypeConfig | null = null;

  if (initialCategoryId) {
    initialCategory = ASSET_CATEGORIES.find((c) => c.id === initialCategoryId) || null;
  }

  if (initialTypeId) {
    for (const cat of ASSET_CATEGORIES) {
      const found = cat.types.find((t) => t.id === initialTypeId);
      if (found) {
        initialType = found;
        if (!initialCategory) initialCategory = cat;
        break;
      }
    }

    if (!initialType) {
      initialType = {
        id: initialTypeId as any,
        name: initialTypeId,
        description: 'Unknown asset product',
        hasContractualMaturity: false,
        supportsFutureProjection: false,
        requiresMarketData: false,
        defaultValuationMethod: 'MANUAL',
      };
    }
  }

  // Determine starting step based on provided query context
  const getInitialStep = (): FlowStep => {
    if (initialPortfolio && initialCategory && initialType) return 'form';
    if (initialPortfolio && initialCategory) return 'type';
    if (initialPortfolio) return 'category';
    return 'portfolio';
  };

  const [step, setStep] = useState<FlowStep>(getInitialStep);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(initialPortfolio);
  const [selectedCategory, setSelectedCategory] = useState<AssetCategoryConfig | null>(initialCategory);
  const [selectedType, setSelectedType] = useState<AssetTypeConfig | null>(initialType);
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const init: Record<string, any> = {};
    if (initialSymbol) {
      init.symbol = initialSymbol;
    }
    if (initialName) {
      init.company_name = initialName;
      init.scheme_name = initialName;
      init.account_nickname = initialName;
      init.property_name = initialName;
    }
    if (initialInstrumentId) {
      init.instrument = initialInstrumentId;
      init.instrument_id = initialInstrumentId;
    }
    return init;
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const createInvestmentMutation = useCreateInvestment();

  // Sync if portfolios load asynchronously
  useEffect(() => {
    if (!selectedPortfolio && portfolios.length > 0) {
      const matched = initialPortfolioId ? portfolios.find((p) => p.id === initialPortfolioId) : null;
      if (matched) {
        setSelectedPortfolio(matched);
      } else if (portfolios.length === 1) {
        setSelectedPortfolio(portfolios[0]);
      }
    }
  }, [portfolios, initialPortfolioId, selectedPortfolio]);

  // Handlers
  const handleSelectPortfolio = (portfolio: Portfolio) => {
    setSelectedPortfolio(portfolio);
    onNavigateStep?.({ portfolioId: portfolio.id });
    setStep('category');
  };

  const handleSelectCategory = (category: AssetCategoryConfig) => {
    if (selectedCategory?.id !== category.id) {
      setSelectedType(null);
      setFormData((prev) => {
        const preserved: Record<string, any> = {};
        if (prev.portfolio_id) preserved.portfolio_id = prev.portfolio_id;
        if (prev.currency) preserved.currency = prev.currency;
        if (prev.notes) preserved.notes = prev.notes;
        return preserved;
      });
    }
    setSelectedCategory(category);
    onNavigateStep?.({ portfolioId: selectedPortfolio?.id, category: category.id });
    setStep('type');
  };

  const handleSelectType = (type: AssetTypeConfig) => {
    if (selectedType?.id !== type.id) {
      setFormData((prev) => {
        const preserved: Record<string, any> = {};
        if (prev.portfolio_id) preserved.portfolio_id = prev.portfolio_id;
        if (prev.currency) preserved.currency = prev.currency;
        if (prev.notes) preserved.notes = prev.notes;
        return preserved;
      });
    }
    setSelectedType(type);
    onNavigateStep?.({
      portfolioId: selectedPortfolio?.id,
      category: selectedCategory?.id,
      type: type.id,
    });
    setStep('form');
  };

  const handleFormSubmit = (data: Record<string, any>) => {
    setFormData((prev) => ({
      ...prev,
      ...data,
      ...(initialInstrumentId ? { instrument: initialInstrumentId, instrument_id: initialInstrumentId } : {}),
    }));
    setSubmitError(null);
    setStep('review');
  };

  const handleConfirmInvestment = async () => {
    if (!selectedPortfolio || !selectedCategory || !selectedType) return;
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await createInvestmentMutation.mutateAsync({
        portfolio: selectedPortfolio.id,
        instrument: initialInstrumentId || formData.instrument || formData.instrument_id || undefined,
        category: selectedCategory.id,
        asset_type: selectedType.id,
        currency: formData.currency || selectedPortfolio.base_currency || 'INR',
        notes: formData.notes || '',
        valuation_method: selectedType.defaultValuationMethod || 'MANUAL',
        details: formData,
      });
      setStep('success');
    } catch (err: any) {
      let errorMsg = err?.message;
      if (err?.data && typeof err.data === 'object') {
        if (err.data.detail) {
          errorMsg = Array.isArray(err.data.detail) ? err.data.detail.join(' ') : String(err.data.detail);
        } else if (err.data.details && typeof err.data.details === 'object') {
          const detailErrors = Object.entries(err.data.details)
            .map(([field, msgs]) => `${field.replace(/_/g, ' ')}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
            .join(' | ');
          errorMsg = `Validation error in details: ${detailErrors}`;
        } else if (err.data.non_field_errors) {
          errorMsg = Array.isArray(err.data.non_field_errors)
            ? err.data.non_field_errors.join(' ')
            : String(err.data.non_field_errors);
        }
      }
      setSubmitError(errorMsg || 'Failed to save investment. Please check the entered data.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedCategory(null);
    setSelectedType(null);
    setFormData({});
    onNavigateStep?.({ portfolioId: selectedPortfolio?.id });
    setStep(portfolios.length > 1 ? 'portfolio' : 'category');
  };

  // Render form dynamically by asset type id
  const renderAssetForm = () => {
    if (!selectedPortfolio || !selectedType) return null;

    const commonProps = {
      portfolioId: selectedPortfolio.id,
      defaultCurrency: selectedPortfolio.base_currency,
      onBack: () => {
        setStep('type');
        onNavigateStep?.({
          portfolioId: selectedPortfolio.id,
          category: selectedCategory?.id,
        });
      },
      isSubmitting,
    };

    switch (selectedType.id) {
      // 1. Cash & Banking
      case 'savings_account':
        return (
          <SavingsAccountForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'current_account':
        return (
          <CurrentAccountForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'cash_balance':
        return (
          <CurrentAccountForm
            {...commonProps}
            initialValues={{
              account_nickname: 'Physical Cash Balance',
              ...formData,
            }}
            onSubmit={handleFormSubmit}
          />
        );

      // 2. Fixed Income
      case 'fixed_deposit':
        return (
          <FixedDepositForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'recurring_deposit':
        return (
          <RecurringDepositForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'bond':
        return (
          <BondForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );

      // 3. Listed Equities & Stocks
      case 'listed_stock':
      case 'stock':
        return (
          <StockForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );

      // 4. Mutual Funds
      case 'mutual_fund':
        return (
          <MutualFundForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );

      // 5. Gold & Bullion
      case 'physical_gold':
        return (
          <PhysicalGoldForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'digital_gold':
        return (
          <DigitalGoldForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'gold_etf':
        return (
          <GoldETFForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );
      case 'sovereign_gold_bond':
        return (
          <SovereignGoldBondForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );

      // 6. Real Estate
      case 'residential_property':
      case 'real_estate':
        return (
          <RealEstateForm
            {...commonProps}
            initialValues={{
              property_type: 'RESIDENTIAL',
              ...formData,
            }}
            onSubmit={handleFormSubmit}
          />
        );
      case 'commercial_property':
        return (
          <RealEstateForm
            {...commonProps}
            initialValues={{
              property_type: 'COMMERCIAL',
              ...formData,
            }}
            onSubmit={handleFormSubmit}
          />
        );
      case 'land_plot':
        return (
          <AgriculturalLandForm
            {...commonProps}
            initialValues={{
              property_type: 'LAND',
              ...formData,
            }}
            onSubmit={handleFormSubmit}
          />
        );

      // 7. Cryptocurrency
      case 'cryptocurrency':
        return (
          <CryptocurrencyForm
            {...commonProps}
            initialValues={formData}
            onSubmit={handleFormSubmit}
          />
        );

      default:
        return (
          <div data-testid="unsupported-asset-state" style={{ padding: '2rem', textAlign: 'center' }}>
            <p>Unsupported asset type: {selectedType.name}</p>
            <Button
              onClick={() => {
                setStep('type');
                onNavigateStep?.({
                  portfolioId: selectedPortfolio.id,
                  category: selectedCategory?.id,
                });
              }}
            >
              Back to Asset Products
            </Button>
          </div>
        );
    }
  };

  // Step indices
  const stepOrder: FlowStep[] = ['portfolio', 'category', 'type', 'form', 'review'];
  const currentStepIndex = stepOrder.indexOf(step);

  return (
    <div className={styles.flowContainer}>
      {/* Stepper Header (Only shown during input workflow) */}
      {step !== 'success' && (
        <div className={styles.stepper}>
          <div
            className={`${styles.stepItem} ${
              step === 'portfolio'
                ? styles.activeStep
                : currentStepIndex > 0
                ? styles.completedStep
                : ''
            }`}
          >
            <div className={styles.stepCircle}>
              {currentStepIndex > 0 ? <Check size={14} /> : '1'}
            </div>
            <span className={styles.stepLabel}>Portfolio</span>
          </div>

          <div className={styles.stepDivider} />

          <div
            className={`${styles.stepItem} ${
              step === 'category'
                ? styles.activeStep
                : currentStepIndex > 1
                ? styles.completedStep
                : ''
            }`}
          >
            <div className={styles.stepCircle}>
              {currentStepIndex > 1 ? <Check size={14} /> : '2'}
            </div>
            <span className={styles.stepLabel}>Category</span>
          </div>

          <div className={styles.stepDivider} />

          <div
            className={`${styles.stepItem} ${
              step === 'type'
                ? styles.activeStep
                : currentStepIndex > 2
                ? styles.completedStep
                : ''
            }`}
          >
            <div className={styles.stepCircle}>
              {currentStepIndex > 2 ? <Check size={14} /> : '3'}
            </div>
            <span className={styles.stepLabel}>Asset Product</span>
          </div>

          <div className={styles.stepDivider} />

          <div
            className={`${styles.stepItem} ${
              step === 'form'
                ? styles.activeStep
                : currentStepIndex > 3
                ? styles.completedStep
                : ''
            }`}
          >
            <div className={styles.stepCircle}>
              {currentStepIndex > 3 ? <Check size={14} /> : '4'}
            </div>
            <span className={styles.stepLabel}>Asset Details</span>
          </div>

          <div className={styles.stepDivider} />

          <div
            className={`${styles.stepItem} ${
              step === 'review' ? styles.activeStep : ''
            }`}
          >
            <div className={styles.stepCircle}>5</div>
            <span className={styles.stepLabel}>Review</span>
          </div>
        </div>
      )}

      {/* Breadcrumb Navigation if inside flow */}
      {selectedPortfolio && step !== 'portfolio' && step !== 'success' && (
        <div className={styles.breadcrumbBar}>
          <button
            type="button"
            className={styles.breadcrumbLink}
            onClick={() => {
              setSelectedCategory(null);
              setSelectedType(null);
              setFormData({});
              onNavigateStep?.({ portfolioId: selectedPortfolio.id });
              setStep('category');
            }}
          >
            {selectedPortfolio.name}
          </button>
          {selectedCategory && (
            <>
              <ChevronRight size={14} />
              <button
                type="button"
                className={styles.breadcrumbLink}
                onClick={() => {
                  setSelectedType(null);
                  setFormData({});
                  onNavigateStep?.({
                    portfolioId: selectedPortfolio.id,
                    category: selectedCategory.id,
                  });
                  setStep('type');
                }}
              >
                {selectedCategory.name}
              </button>
            </>
          )}
          {selectedType && (
            <>
              <ChevronRight size={14} />
              <button
                type="button"
                className={styles.breadcrumbLink}
                onClick={() => {
                  setFormData({});
                  onNavigateStep?.({
                    portfolioId: selectedPortfolio.id,
                    category: selectedCategory?.id,
                    type: selectedType.id,
                  });
                  setStep('form');
                }}
              >
                {selectedType.name}
              </button>
            </>
          )}
        </div>
      )}

      {/* Step Content */}
      {step === 'portfolio' && (
        <PortfolioSelector
          portfolios={portfolios}
          selectedPortfolioId={selectedPortfolio?.id}
          onSelectPortfolio={handleSelectPortfolio}
          isLoading={isLoadingPortfolios}
        />
      )}

      {step === 'category' && (
        <AssetCategorySelector
          selectedCategoryId={selectedCategory?.id}
          onSelectCategory={handleSelectCategory}
        />
      )}

      {step === 'type' && selectedCategory && (
        <AssetTypeSelector
          category={selectedCategory}
          selectedTypeId={selectedType?.id}
          onSelectType={handleSelectType}
        />
      )}

      {step === 'form' && renderAssetForm()}

      {step === 'review' && selectedPortfolio && selectedCategory && selectedType && (
        <div>
          {submitError && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
              {submitError}
            </div>
          )}
          <InvestmentReview
            portfolio={selectedPortfolio}
            category={selectedCategory}
            type={selectedType}
            formData={formData}
            onConfirm={handleConfirmInvestment}
            onEdit={() => setStep('form')}
            isSubmitting={isSubmitting}
          />
        </div>
      )}

      {step === 'success' && (
        <div className={styles.successCard}>
          <div className={styles.successIcon}>
            <CheckCircle2 size={32} />
          </div>
          <h2 className={styles.successTitle}>Investment Persisted Successfully</h2>
          <p className={styles.successDesc}>
            Your {selectedType?.name} entry has been securely saved to the portfolio ledger and linked to{' '}
            <strong>{selectedPortfolio?.name}</strong>.
          </p>
          <div className={styles.successActions}>
            <Button
              variant="primary"
              onClick={() => navigate(`/portfolios/${selectedPortfolio?.id}`)}
            >
              View in Portfolio
            </Button>
            <Button variant="outline" onClick={handleReset}>
              Add Another Investment
            </Button>
            <Button variant="secondary" onClick={() => navigate('/dashboard')}>
              Dashboard
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
