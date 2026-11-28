export interface AIExplanation {
  answer: string;
  key_points: string[];
  limitations: string[];
  referenced_metrics: string[];
  disclaimer: string;
}

export interface AIUsage {
  model: string;
  latency_seconds: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  is_configured: boolean;
}

export interface AIExplainResponse {
  explanation: AIExplanation;
  usage: AIUsage;
}

export interface AIExplainPayload {
  portfolio_id: string;
  investment_id?: string;
  question: string;
  focus_area?: string;
  as_of_date?: string;
}

export interface AIStatusResponse {
  is_configured: boolean;
  model: string;
}
