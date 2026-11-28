import React, { useState } from 'react';
import {
  Sparkles,
  X,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Info,
  RefreshCw,
  Cpu,
} from 'lucide-react';
import { useAiExplain, useAiStatus } from '../api/aiApi';
import { AIExplainResponse } from '../types';

interface AiAssistantModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: string;
  portfolioName?: string;
  investmentId?: string;
  investmentName?: string;
}

const SUGGESTED_PROMPTS = [
  'Explain my return breakdown and overall portfolio growth.',
  'What is driving the gap between my realized and unrealized gains?',
  'How well diversified is my current asset allocation?',
  'Explain the difference between my money-weighted XIRR and time-weighted returns.',
];

const FOCUS_AREAS = [
  { id: '', label: 'General' },
  { id: 'performance', label: 'Performance' },
  { id: 'allocation', label: 'Allocation' },
  { id: 'risk', label: 'Risk & Limits' },
];

export const AiAssistantModal: React.FC<AiAssistantModalProps> = ({
  isOpen,
  onClose,
  portfolioId,
  portfolioName,
  investmentId,
  investmentName,
}) => {
  const [question, setQuestion] = useState<string>('');
  const [focusArea, setFocusArea] = useState<string>('');
  const [result, setResult] = useState<AIExplainResponse | null>(null);

  const { data: statusData } = useAiStatus();
  const explainMutation = useAiExplain();

  if (!isOpen) return null;

  const handleAsk = (promptText?: string) => {
    const q = promptText || question;
    if (!q.trim() || explainMutation.isPending) return;

    explainMutation.mutate(
      {
        portfolio_id: portfolioId,
        investment_id: investmentId,
        question: q.trim(),
        focus_area: focusArea || undefined,
      },
      {
        onSuccess: (data) => {
          setResult(data);
          if (promptText) setQuestion(promptText);
        },
      }
    );
  };

  // Simple Markdown-to-HTML parser for safe educational formatting
  const renderFormattedText = (text: string) => {
    const paragraphs = text.split('\n\n');
    return paragraphs.map((para, idx) => {
      // Check if bullet list
      if (para.startsWith('- ') || para.startsWith('* ')) {
        const items = para.split('\n').filter((l) => l.trim().length > 0);
        return (
          <ul key={idx} className="list-disc pl-5 space-y-1 my-2 text-theme-text text-sm">
            {items.map((item, itemIdx) => (
              <li key={itemIdx}>{item.replace(/^[-*]\s+/, '').replace(/\*\*(.*?)\*\*/g, '$1')}</li>
            ))}
          </ul>
        );
      }
      return (
        <p key={idx} className="text-theme-text text-sm leading-relaxed mb-3">
          {para.replace(/\*\*(.*?)\*\*/g, '$1')}
        </p>
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-theme-surface border border-theme-border rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border bg-theme-surface">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-600 flex items-center justify-center">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-theme-text">AI Financial Insights</h2>
                {statusData?.model && (
                  <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-theme-primary/10 text-theme-primary border border-theme-primary/20">
                    {statusData.model}
                  </span>
                )}
              </div>
              <p className="text-xs text-theme-text-muted">
                {investmentName
                  ? `Holding: ${investmentName}`
                  : `Portfolio: ${portfolioName || 'Current Portfolio'}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-theme-text-muted hover:text-theme-text rounded-xl hover:bg-theme-border/50 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Unconfigured Alert Banner */}
          {statusData && !statusData.is_configured && (
            <div className="flex items-start space-x-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-600 text-xs">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">AI Explanations Inactive</p>
                <p className="mt-0.5 text-theme-text-muted">
                  OpenAI API key is not configured on this server. Standard calculated metrics are fully active, but generative narrative insights are disabled.
                </p>
              </div>
            </div>
          )}

          {/* Result Presentation */}
          {result && (
            <div className="space-y-4">
              {/* Answer narrative */}
              <div className="p-5 rounded-2xl bg-theme-background border border-theme-border">
                <div className="flex items-center justify-between mb-3 border-b border-theme-border/50 pb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-theme-primary flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" /> Analytical Explanation
                  </span>
                  {result.usage && (
                    <span className="text-[10px] text-theme-text-muted flex items-center gap-1">
                      <Cpu className="h-3 w-3" /> {result.usage.latency_seconds}s • {result.usage.total_tokens} tokens
                    </span>
                  )}
                </div>
                {renderFormattedText(result.explanation.answer)}

                {/* Referenced metrics pills */}
                {result.explanation.referenced_metrics?.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-theme-border/50 mt-3">
                    <span className="text-[11px] font-medium text-theme-text-muted mr-1">Cited metrics:</span>
                    {result.explanation.referenced_metrics.map((m) => (
                      <span
                        key={m}
                        className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-theme-surface border border-theme-border text-theme-text"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Key points */}
              {result.explanation.key_points?.length > 0 && (
                <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                  <h4 className="text-xs font-bold text-emerald-600 flex items-center gap-1.5 mb-2">
                    <CheckCircle2 className="h-4 w-4" /> Key Observations
                  </h4>
                  <ul className="space-y-1.5">
                    {result.explanation.key_points.map((pt, i) => (
                      <li key={i} className="text-xs text-theme-text flex items-start gap-2">
                        <span className="text-emerald-500 font-bold shrink-0">•</span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Limitations & Caveats */}
              {result.explanation.limitations?.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
                  <h4 className="text-xs font-bold text-amber-600 flex items-center gap-1.5 mb-1.5">
                    <AlertTriangle className="h-4 w-4" /> Data Completeness & Limitations
                  </h4>
                  <ul className="space-y-1">
                    {result.explanation.limitations.map((lim, i) => (
                      <li key={i} className="text-xs text-theme-text-muted flex items-start gap-2">
                        <span className="text-amber-500 shrink-0">•</span>
                        <span>{lim}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Regulatory Non-Advisory Disclaimer */}
              <div className="p-3 rounded-xl bg-theme-surface border border-theme-border/50 text-[11px] text-theme-text-muted italic flex items-start gap-2">
                <Info className="h-4 w-4 shrink-0 mt-0.5 text-theme-text-muted" />
                <span>{result.explanation.disclaimer}</span>
              </div>
            </div>
          )}

          {/* Loading State */}
          {explainMutation.isPending && (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
              <p className="text-xs font-medium text-theme-text animate-pulse">
                Analyzing verified portfolio transactions and performance metrics...
              </p>
              <p className="text-[11px] text-theme-text-muted">
                Synthesizing context-grounded explanation via OpenAI Responses API.
              </p>
            </div>
          )}

          {/* Error Message */}
          {explainMutation.isError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 text-xs flex items-start justify-between">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Unable to Generate Explanation</p>
                  <p className="mt-0.5 text-theme-text-muted">
                    {explainMutation.error?.message || 'An unexpected error occurred while communicating with the AI service.'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleAsk()}
                className="px-2.5 py-1 text-xs font-medium bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition flex items-center gap-1 shrink-0"
              >
                <RefreshCw className="h-3 w-3" /> Retry
              </button>
            </div>
          )}

          {/* Focus Area Selection & Suggested Prompts */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-theme-text-muted">Focus area:</span>
              <div className="flex items-center gap-1.5">
                {FOCUS_AREAS.map((fa) => (
                  <button
                    key={fa.id}
                    onClick={() => setFocusArea(fa.id)}
                    className={`text-[11px] px-2.5 py-1 rounded-lg font-medium transition ${
                      focusArea === fa.id
                        ? 'bg-purple-600 text-white'
                        : 'bg-theme-background border border-theme-border text-theme-text hover:bg-theme-surface'
                    }`}
                  >
                    {fa.label}
                  </button>
                ))}
              </div>
            </div>

            <span className="text-xs font-semibold text-theme-text-muted block">Suggested questions:</span>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  disabled={explainMutation.isPending}
                  onClick={() => handleAsk(prompt)}
                  className="text-xs px-3 py-1.5 rounded-xl border border-theme-border bg-theme-background hover:bg-theme-surface text-theme-text hover:border-theme-primary/40 transition-colors text-left"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Input Footer */}
        <div className="p-4 border-t border-theme-border bg-theme-surface">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAsk();
              }}
              placeholder="Ask an analytical question about your performance, allocation, or returns..."
              disabled={explainMutation.isPending}
              className="flex-1 text-xs px-4 py-2.5 rounded-xl border border-theme-border bg-theme-background text-theme-text focus:outline-none focus:border-theme-primary transition-colors disabled:opacity-50"
            />
            <button
              onClick={() => handleAsk()}
              disabled={!question.trim() || explainMutation.isPending}
              className="px-4 py-2.5 bg-theme-primary text-white rounded-xl text-xs font-semibold hover:bg-theme-primary/90 transition flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              {explainMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
              Explain
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
