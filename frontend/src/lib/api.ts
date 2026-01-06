import { Token, User, Watchlist, News, NewsListResponse, ResearchTask } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private accessToken: string | null = null;

  setToken(token: string) {
    this.accessToken = token;
  }

  clearToken() {
    this.accessToken = null;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${API_URL}/api/v1${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json();
  }

  // Auth
  async register(email: string, password: string, name: string): Promise<User> {
    return this.fetch<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
  }

  async login(email: string, password: string): Promise<Token> {
    return this.fetch<Token>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.fetch<User>("/auth/me");
  }

  // Settings API
  async updateNotificationPreferences(preferences: {
    news_alerts?: boolean;
    filing_alerts?: boolean;
    research_complete?: boolean;
  }): Promise<User> {
    return this.fetch<User>("/auth/settings", {
      method: "PATCH",
      body: JSON.stringify({ notification_preferences: preferences }),
    });
  }

  async generateTelegramLink(): Promise<{ link: string; expires_in: number }> {
    return this.fetch("/auth/telegram/link", {
      method: "POST",
    });
  }

  async connectTelegram(chatId: string): Promise<User> {
    return this.fetch<User>("/auth/telegram/connect", {
      method: "POST",
      body: JSON.stringify({ chat_id: chatId }),
    });
  }

  async disconnectTelegram(): Promise<User> {
    return this.fetch<User>("/auth/telegram/disconnect", {
      method: "DELETE",
    });
  }

  // Watchlists
  async getWatchlists(): Promise<Watchlist[]> {
    return this.fetch<Watchlist[]>("/watchlists");
  }

  async createWatchlist(name: string, description?: string): Promise<Watchlist> {
    return this.fetch<Watchlist>("/watchlists", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });
  }

  async getWatchlist(id: string): Promise<Watchlist> {
    return this.fetch<Watchlist>(`/watchlists/${id}`);
  }

  async deleteWatchlist(id: string): Promise<void> {
    return this.fetch<void>(`/watchlists/${id}`, {
      method: "DELETE",
    });
  }

  async addStockToWatchlist(watchlistId: string, ticker: string, notes?: string): Promise<void> {
    return this.fetch<void>(`/watchlists/${watchlistId}/items`, {
      method: "POST",
      body: JSON.stringify({ ticker, notes }),
    });
  }

  async removeStockFromWatchlist(watchlistId: string, ticker: string): Promise<void> {
    return this.fetch<void>(`/watchlists/${watchlistId}/items/${ticker}`, {
      method: "DELETE",
    });
  }

  // News
  async getNews(params?: { ticker?: string; watchlist_id?: string; page?: number; page_size?: number }): Promise<NewsListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.ticker) searchParams.set("ticker", params.ticker);
    if (params?.watchlist_id) searchParams.set("watchlist_id", params.watchlist_id);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));

    return this.fetch<NewsListResponse>(`/news?${searchParams.toString()}`);
  }

  async getNewsForTicker(ticker: string, limit = 20): Promise<News[]> {
    return this.fetch<News[]>(`/news/ticker/${ticker}?limit=${limit}`);
  }

  // Research
  async getResearchTasks(params?: { status?: string; task_type?: string; limit?: number }): Promise<ResearchTask[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status_filter", params.status);
    if (params?.task_type) searchParams.set("task_type", params.task_type);
    if (params?.limit) searchParams.set("limit", String(params.limit));

    return this.fetch<ResearchTask[]>(`/research?${searchParams.toString()}`);
  }

  async createDiscoveryTask(params: {
    title: string;
    theme: string;
    market_cap_min?: number;
    market_cap_max?: number;
    sectors?: string[];
    additional_criteria?: string;
  }): Promise<ResearchTask> {
    return this.fetch<ResearchTask>("/research/discovery", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async createDeepDiveTask(params: {
    title: string;
    ticker: string;
    focus_areas?: string[];
  }): Promise<ResearchTask> {
    return this.fetch<ResearchTask>("/research/deep-dive", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getResearchTask(id: string): Promise<ResearchTask> {
    return this.fetch<ResearchTask>(`/research/${id}`);
  }

  async cancelResearchTask(id: string): Promise<ResearchTask> {
    return this.fetch<ResearchTask>(`/research/${id}/cancel`, {
      method: "POST",
    });
  }

  // Stocks
  async searchStocks(query: string, limit = 10): Promise<{ ticker: string; name: string | null; type: string | null }[]> {
    return this.fetch(`/stocks/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }
}

export const api = new ApiClient();
