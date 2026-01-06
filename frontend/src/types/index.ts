export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  settings: UserSettings;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  telegram_chat_id?: string;
  notification_preferences?: {
    news_alerts: boolean;
    filing_alerts: boolean;
    research_complete: boolean;
  };
}

export interface Stock {
  ticker: string;
  company_name: string;
  sector?: string;
  industry?: string;
  cik?: string;
  market_cap?: number;
  exchange?: string;
  metadata_: Record<string, unknown>;
  last_updated: string;
}

export interface WatchlistItem {
  id: string;
  ticker: string;
  notes?: string;
  added_at: string;
  stock?: Stock;
}

export interface Watchlist {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  items: WatchlistItem[];
}

export interface News {
  id: string;
  ticker: string;
  headline: string;
  summary?: string;
  url: string;
  source: string;
  published_at: string;
  ai_summary?: string;
  sentiment?: "bullish" | "bearish" | "neutral";
  importance?: "high" | "medium" | "low";
  ai_analysis: Record<string, unknown>;
  created_at: string;
}

export interface NewsListResponse {
  items: News[];
  total: number;
  page: number;
  page_size: number;
}

export interface ResearchTask {
  id: string;
  task_type: "discovery" | "deep_dive" | "earnings_analysis" | "filing_analysis" | "comparative";
  title: string;
  description?: string;
  parameters: Record<string, unknown>;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  error_message?: string;
  results: Record<string, unknown>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
