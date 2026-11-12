import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Edit2, Loader2 } from 'lucide-react';
import { portfolioFormSchema, PortfolioFormData } from '../schemas/portfolioSchema';
import { usePortfolio, useUpdatePortfolio } from '../hooks/usePortfolios';
import { SUPPORTED_CURRENCIES, SupportedCurrency } from '../types';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';

export const PortfolioEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: portfolio, isLoading, isError } = usePortfolio(id || '');
  const { mutate: updatePortfolio, isPending } = useUpdatePortfolio();
  const [serverError, setServerError] = useState<string>('');

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PortfolioFormData>({
    resolver: zodResolver(portfolioFormSchema),
  });

  useEffect(() => {
    if (portfolio) {
      reset({
        name: portfolio.name,
        description: portfolio.description || '',
        base_currency: portfolio.base_currency,
      });
    }
  }, [portfolio, reset]);

  const onSubmit = (data: PortfolioFormData) => {
    if (!id) return;
    setServerError('');
    updatePortfolio(
      {
        id,
        payload: {
          name: data.name,
          description: data.description || '',
          base_currency: data.base_currency as SupportedCurrency,
        },
      },
      {
        onSuccess: () => {
          navigate(`/portfolios/${id}`);
        },
        onError: (err: any) => {
          setServerError(err?.message || 'Failed to update portfolio.');
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-theme-text-muted">
        <Loader2 className="h-8 w-8 animate-spin text-theme-primary mb-2" />
        <p className="text-sm">Loading portfolio...</p>
      </div>
    );
  }

  if (isError || !portfolio) {
    return (
      <div className="max-w-md mx-auto text-center py-16 space-y-4">
        <h2 className="text-lg font-semibold text-theme-text">Portfolio not found</h2>
        <p className="text-xs text-theme-text-muted">
          The requested portfolio does not exist or you do not have permission to edit it.
        </p>
        <Link to="/portfolios">
          <Button variant="outline" className="border-theme-border text-theme-text">
            Back to Portfolios
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          to={`/portfolios/${id}`}
          className="inline-flex items-center text-xs font-medium text-theme-text-muted hover:text-theme-text transition-colors"
        >
          <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Portfolio Details
        </Link>
      </div>

      <Card className="border-theme-border bg-theme-card p-6 sm:p-8 backdrop-blur shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-theme-primary-subtle text-theme-primary border border-theme-primary/30">
            <Edit2 className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-xl text-theme-text">Edit Portfolio</CardTitle>
            <CardDescription className="text-xs text-theme-text-muted">
              Update portfolio name, currency, or allocation notes.
            </CardDescription>
          </div>
        </div>

        {serverError && (
          <div className="mb-6 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Portfolio Name */}
          <div className="space-y-1.5">
            <Label htmlFor="name" className="text-xs font-semibold text-theme-text-secondary">
              Portfolio Name <span className="text-theme-negative">*</span>
            </Label>
            <Input
              id="name"
              placeholder="e.g. Long Term Investments"
              {...register('name')}
              className="bg-theme-surface border-theme-border text-theme-text"
            />
            {errors.name && (
              <p className="text-xs text-theme-negative">{errors.name.message}</p>
            )}
          </div>

          {/* Base Currency */}
          <div className="space-y-1.5">
            <Label htmlFor="base_currency" className="text-xs font-semibold text-theme-text-secondary">
              Base Currency <span className="text-theme-negative">*</span>
            </Label>
            <select
              id="base_currency"
              {...register('base_currency')}
              className="w-full rounded-md border border-theme-border bg-theme-surface px-3 py-2 text-sm text-theme-text focus:outline-none focus:ring-2 focus:ring-theme-primary"
            >
              {SUPPORTED_CURRENCIES.map((curr) => (
                <option key={curr.code} value={curr.code} className="bg-theme-card text-theme-text">
                  {curr.code} — {curr.name} ({curr.symbol})
                </option>
              ))}
            </select>
            {errors.base_currency && (
              <p className="text-xs text-theme-negative">{errors.base_currency.message}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label htmlFor="description" className="text-xs font-semibold text-theme-text-secondary">
              Description <span className="text-theme-text-muted font-normal">(optional)</span>
            </Label>
            <textarea
              id="description"
              rows={3}
              placeholder="Investment notes..."
              {...register('description')}
              className="w-full rounded-md border border-theme-border bg-theme-surface px-3 py-2 text-sm text-theme-text placeholder:text-theme-text-muted focus:outline-none focus:ring-2 focus:ring-theme-primary resize-none"
            />
            {errors.description && (
              <p className="text-xs text-theme-negative">{errors.description.message}</p>
            )}
          </div>

          {/* Buttons */}
          <div className="pt-4 flex items-center justify-end gap-3 border-t border-theme-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(`/portfolios/${id}`)}
              disabled={isPending}
              className="border-theme-border text-theme-text-muted hover:text-theme-text"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending}
              className="bg-theme-primary text-theme-text-inverse hover:bg-theme-primary-hover shadow-sm"
            >
              {isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Updating...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
