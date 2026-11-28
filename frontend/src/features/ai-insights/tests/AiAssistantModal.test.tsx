import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AiAssistantModal } from '../components/AiAssistantModal';
import * as aiApi from '../api/aiApi';

vi.mock('../api/aiApi', () => ({
  useAiStatus: vi.fn(),
  useAiExplain: vi.fn(),
}));

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('AiAssistantModal', () => {
  it('does not render when isOpen is false', () => {
    (aiApi.useAiStatus as any).mockReturnValue({
      data: { is_configured: true, model: 'gpt-4o-mini' },
    });
    (aiApi.useAiExplain as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
    });

    renderWithProviders(
      <AiAssistantModal
        isOpen={false}
        onClose={vi.fn()}
        portfolioId="p-123"
        portfolioName="My Wealth"
      />
    );

    expect(screen.queryByText('AI Financial Insights')).not.toBeInTheDocument();
  });

  it('renders modal and unconfigured warning when OpenAI is disabled', () => {
    (aiApi.useAiStatus as any).mockReturnValue({
      data: { is_configured: false, model: 'gpt-4o-mini' },
    });
    (aiApi.useAiExplain as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
    });

    renderWithProviders(
      <AiAssistantModal
        isOpen={true}
        onClose={vi.fn()}
        portfolioId="p-123"
        portfolioName="My Wealth"
      />
    );

    expect(screen.getByText('AI Financial Insights')).toBeInTheDocument();
    expect(screen.getByText('AI Explanations Inactive')).toBeInTheDocument();
    expect(screen.getByText(/Portfolio: My Wealth/i)).toBeInTheDocument();
  });

  it('allows clicking a suggested prompt and triggers mutation', () => {
    const mockMutate = vi.fn();
    (aiApi.useAiStatus as any).mockReturnValue({
      data: { is_configured: true, model: 'gpt-4o-mini' },
    });
    (aiApi.useAiExplain as any).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: false,
    });

    renderWithProviders(
      <AiAssistantModal
        isOpen={true}
        onClose={vi.fn()}
        portfolioId="p-123"
        portfolioName="My Wealth"
      />
    );

    const promptBtn = screen.getByText('Explain my return breakdown and overall portfolio growth.');
    fireEvent.click(promptBtn);

    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        portfolio_id: 'p-123',
        question: 'Explain my return breakdown and overall portfolio growth.',
      }),
      expect.anything()
    );
  });
});
