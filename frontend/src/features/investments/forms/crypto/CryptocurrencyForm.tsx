import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Calculator } from 'lucide-react';
import {
  cryptocurrencySchema,
  CryptocurrencyFormData,
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

const NETWORK_OPTIONS = [
  { value: 'Bitcoin', label: 'Bitcoin (Native L1)' },
  { value: 'Ethereum', label: 'Ethereum (ERC-20)' },
  { value: 'Solana', label: 'Solana (SPL)' },
  { value: 'Polygon', label: 'Polygon (POS)' },
  { value: 'Binance Smart Chain', label: 'BNB Smart Chain (BEP-20)' },
  { value: 'Arbitrum', label: 'Arbitrum One (L2)' },
  { value: 'Other Network', label: 'Other Blockchain Network' },
];

const WALLET_TYPE_OPTIONS = [
  { value: 'HARDWARE_WALLET', label: 'Hardware Cold Wallet (Ledger / Trezor)' },
  { value: 'SOFTWARE_WALLET', label: 'Self-Custody Software Wallet (Metamask / Phantom)' },
  { value: 'EXCHANGE', label: 'Centralized Exchange (CEX)' },
  { value: 'OTHER', label: 'Other Custodial Solution' },
];

export interface CryptocurrencyFormProps {
  portfolioId: string;
  defaultCurrency?: string;
  initialValues?: Partial<CryptocurrencyFormData>;
  onSubmit: (data: CryptocurrencyFormData) => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export const CryptocurrencyForm: React.FC<CryptocurrencyFormProps> = ({
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
  } = useForm<CryptocurrencyFormData>({
    resolver: zodResolver(cryptocurrencySchema),
    defaultValues: {
      portfolio_id: portfolioId,
      token_name: initialValues?.token_name || '',
      symbol: initialValues?.symbol || '',
      network: initialValues?.network || 'Bitcoin',
      contract_address: initialValues?.contract_address || '',
      quantity: initialValues?.quantity ?? 0.5,
      purchase_price_per_token: initialValues?.purchase_price_per_token ?? 5000000,
      currency: (initialValues?.currency || defaultCurrency) as any,
      purchase_date: initialValues?.purchase_date || new Date().toISOString().split('T')[0],
      wallet_type: initialValues?.wallet_type || 'EXCHANGE',
      exchange_name: initialValues?.exchange_name || 'CoinDCX',
      transaction_hash: initialValues?.transaction_hash || '',
      notes: initialValues?.notes || '',
    },
  });

  const quantity = watch('quantity') || 0;
  const price = watch('purchase_price_per_token') || 0;
  const currency = watch('currency') || 'INR';
  const totalCost = quantity * price;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.formContainer} noValidate>
      <FormSection
        title="Crypto Asset & Protocol"
        description="Token identity, blockchain network, and ticker symbol."
        columns={2}
      >
        <FormField
          label="Token Name"
          htmlFor="token_name"
          required
          error={errors.token_name?.message}
          helperText="e.g. Bitcoin, Ethereum, Solana"
        >
          <input
            id="token_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. Bitcoin"
            {...register('token_name')}
          />
        </FormField>

        <FormField
          label="Ticker Symbol"
          htmlFor="symbol"
          required
          error={errors.symbol?.message}
          helperText="e.g. BTC, ETH, SOL, MATIC"
        >
          <input
            id="symbol"
            type="text"
            className={styles.textInput}
            placeholder="e.g. BTC"
            style={{ textTransform: 'uppercase' }}
            {...register('symbol')}
          />
        </FormField>

        <Controller
          name="network"
          control={control}
          render={({ field }) => (
            <SearchSelect
              label="Settlement Network / Blockchain"
              options={NETWORK_OPTIONS}
              value={field.value}
              onChange={field.onChange}
              error={errors.network?.message}
              required
            />
          )}
        />

        <FormField
          label="Token Contract Address"
          htmlFor="contract_address"
          optional
          error={errors.contract_address?.message}
          helperText="ERC-20 / SPL smart contract address (if applicable)"
        >
          <input
            id="contract_address"
            type="text"
            className={styles.textInput}
            placeholder="0x..."
            {...register('contract_address')}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Holding & Acquisition Cost"
        description="Token units (up to 8 decimals) and acquisition rate."
        columns={2}
      >
        <Controller
          name="quantity"
          control={control}
          render={({ field }) => (
            <NumberInput
              label="Token Quantity"
              value={field.value}
              onChange={field.onChange}
              min={0.00000001}
              precision={8}
              error={errors.quantity?.message}
              required
              helperText="Precision up to 8 decimal places"
            />
          )}
        />

        <Controller
          name="purchase_price_per_token"
          control={control}
          render={({ field }) => (
            <CurrencyInput
              label="Purchase Price per Token"
              value={field.value}
              onChange={field.onChange}
              currency={currency}
              error={errors.purchase_price_per_token?.message}
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
        title="Custody & Storage"
        description="Where your private keys or tokens are held."
        columns={2}
      >
        <FormField label="Custody Type" htmlFor="wallet_type" error={errors.wallet_type?.message}>
          <select id="wallet_type" className={styles.selectInput} {...register('wallet_type')}>
            {WALLET_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </FormField>

        <FormField
          label="Exchange / Wallet Platform"
          htmlFor="exchange_name"
          optional
          error={errors.exchange_name?.message}
          helperText="e.g. CoinDCX, Binance, Ledger Nano X"
        >
          <input
            id="exchange_name"
            type="text"
            className={styles.textInput}
            placeholder="e.g. CoinDCX"
            {...register('exchange_name')}
          />
        </FormField>

        <FormField
          label="Tx Hash / Order Identifier"
          htmlFor="transaction_hash"
          optional
          error={errors.transaction_hash?.message}
          helperText="On-chain tx hash for verification"
        >
          <input
            id="transaction_hash"
            type="text"
            className={styles.textInput}
            placeholder="0x..."
            {...register('transaction_hash')}
          />
        </FormField>
      </FormSection>

      {/* Cost Basis Preview */}
      {totalCost > 0 && (
        <div className={styles.previewCard}>
          <div className={styles.previewHeader}>
            <div className={styles.previewTitle}>
              <Calculator size={16} />
              <span>Crypto Cost Basis Preview</span>
            </div>
            <span className={styles.previewBadge}>Initial Outflow</span>
          </div>
          <div className={styles.previewGrid}>
            <div className={styles.previewItem}>
              <span className={styles.previewItemLabel}>Total Capital Invested</span>
              <span className={styles.previewItemValue}>
                ₹{totalCost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={styles.previewItemSub}>{quantity} tokens</span>
            </div>
          </div>
        </div>
      )}

      <FormSection title="Additional Notes" columns={1}>
        <FormField label="Notes" htmlFor="notes" optional error={errors.notes?.message}>
          <textarea
            id="notes"
            className={styles.textareaInput}
            placeholder="Add tax lot info, hardware wallet memo..."
            {...register('notes')}
          />
        </FormField>
      </FormSection>

      <FormActions onBack={onBack} submitLabel="Review Crypto Holding" isSubmitting={isSubmitting} />
    </form>
  );
};
