import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Briefcase, Loader2 } from 'lucide-react';
import { portfolioFormSchema, PortfolioFormData } from '../schemas/portfolioSchema';
import { useCreatePortfolio } from '../hooks/usePortfolios';
import { SUPPORTED_CURRENCIES, SupportedCurrency } from '../types';
import { Card, CardTitle, CardDescription } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Label } from '@/shared/ui/Label';

export const PortfolioCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { mutate: createPortfolio, isPending } = useCreatePortfolio();
  const [serverError, setServerError] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PortfolioFormData>({
    resolver: zodResolver(portfolioFormSchema),
    defaultValues: {
      name: '',
      description: '',
      base_currency: 'INR',
    },
  });

  const onSubmit = (data: PortfolioFormData) => {
    setServerError('');
    createPortfolio(
      {
        name: data.name,
        description: data.description || '',
        base_currency: data.base_currency as SupportedCurrency,
      },
      {
        onSuccess: (portfolio) => {
          navigate(`/portfolios/${portfolio.id}`, { replace: true });
        },
        onError: (err: any) => {
          setServerError(err?.message || 'Failed to create portfolio. Please check your inputs.');
        },
      }
    );
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          to="/portfolios"
          className="inline-flex items-center text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Portfolios
        </Link>
      </div>

      <Card className="border-slate-800 bg-slate-900/60 p-6 sm:p-8 backdrop-blur">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
            <Briefcase className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-xl text-white">Create New Portfolio</CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Establish a new portfolio container to track assets, transactions, and valuations.
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
            <Label htmlFor="name" className="text-xs font-semibold text-slate-300">
              Portfolio Name <span className="text-rose-400">*</span>
            </Label>
            <Input
              id="name"
              placeholder="e.g. Long Term Investments, US Growth, Retirement"
              {...register('name')}
              className="bg-slate-950/60 border-slate-800 text-white"
            />
            {errors.name && (
              <p className="text-xs text-rose-400">{errors.name.message}</p>
            )}
          </div>

          {/* Base Currency */}
          <div className="space-y-1.5">
            <Label htmlFor="base_currency" className="text-xs font-semibold text-slate-300">
              Base Currency <span className="text-rose-400">*</span>
            </Label>
            <select
              id="base_currency"
              {...register('base_currency')}
              className="w-full rounded-md border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SUPPORTED_CURRENCIES.map((curr) => (
                <option key={curr.code} value={curr.code} className="bg-slate-900 text-white">
                  {curr.code} — {curr.name} ({curr.symbol})
                </option>
              ))}
            </select>
            {errors.base_currency && (
              <p className="text-xs text-rose-400">{errors.base_currency.message}</p>
            )}
            <p className="text-[11px] text-slate-500">
              The primary currency in which total values, performance, and asset weights will be calculated.
            </p>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label htmlFor="description" className="text-xs font-semibold text-slate-300">
              Description <span className="text-slate-500 font-normal">(optional)</span>
            </Label>
            <textarea
              id="description"
              rows={3}
              placeholder="Investment goals, risk tolerance, or notes about this portfolio..."
              {...register('description')}
              className="w-full rounded-md border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
            {errors.description && (
              <p className="text-xs text-rose-400">{errors.description.message}</p>
            )}
          </div>

          {/* Buttons */}
          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/portfolios')}
              disabled={isPending}
              className="border-slate-800 text-slate-400 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              {isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating...
                </>
              ) : (
                'Create Portfolio'
              )}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
