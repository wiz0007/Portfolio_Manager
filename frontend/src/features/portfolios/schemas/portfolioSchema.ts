import { z } from 'zod';

export const portfolioFormSchema = z.object({
  name: z
    .string()
    .min(1, 'Portfolio name is required.')
    .max(100, 'Portfolio name cannot exceed 100 characters.')
    .trim(),
  description: z
    .string()
    .max(1000, 'Description cannot exceed 1000 characters.')
    .default('')
    .optional(),
  base_currency: z.enum(
    ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'SGD', 'CHF', 'AED'] as const,
    {
      errorMap: () => ({ message: 'Please select a supported currency.' }),
    }
  ),
});

export type PortfolioFormData = z.infer<typeof portfolioFormSchema>;
