"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { api } from "@/lib/api";
import { Watchlist, WatchlistItem, News } from "@/types";
import { ArrowLeft, Plus, Trash2, TrendingUp, Building2, RefreshCw, ExternalLink, Search, Loader2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

interface StockSearchResult {
  ticker: string;
  name: string | null;
  type: string | null;
}

export default function WatchlistDetailPage() {
  const params = useParams();
  const router = useRouter();
  const watchlistId = params.id as string;

  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [loading, setLoading] = useState(true);
  const [addStockOpen, setAddStockOpen] = useState(false);
  const [ticker, setTicker] = useState("");
  const [adding, setAdding] = useState(false);
  const [news, setNews] = useState<News[]>([]);
  const [loadingNews, setLoadingNews] = useState(false);

  // Stock search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<StockSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced stock search
  const searchStocks = useCallback(async (query: string) => {
    if (query.length < 1) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const results = await api.searchStocks(query, 10);
      setSearchResults(results);
    } catch (error) {
      console.error("Failed to search stocks:", error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.length >= 1) {
      searchTimeoutRef.current = setTimeout(() => {
        searchStocks(searchQuery);
      }, 300);
    } else {
      setSearchResults([]);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, searchStocks]);

  const fetchWatchlist = async () => {
    try {
      const data = await api.getWatchlist(watchlistId);
      setWatchlist(data);
    } catch (error) {
      toast.error("Failed to load watchlist");
      router.push("/watchlist");
    } finally {
      setLoading(false);
    }
  };

  const fetchNews = async () => {
    if (!watchlist?.items.length) return;

    setLoadingNews(true);
    try {
      const response = await api.getNews({ watchlist_id: watchlistId, page_size: 20 });
      setNews(response.items || []);
    } catch (error) {
      console.error("Failed to load news:", error);
    } finally {
      setLoadingNews(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, [watchlistId]);

  useEffect(() => {
    if (watchlist) {
      fetchNews();
    }
  }, [watchlist]);

  const handleAddStock = async (selectedTicker?: string) => {
    const tickerToAdd = selectedTicker || ticker.trim().toUpperCase();
    if (!tickerToAdd) return;

    setAdding(true);
    try {
      await api.addStockToWatchlist(watchlistId, tickerToAdd);
      toast.success(`Added ${tickerToAdd} to watchlist`);
      setTicker("");
      setSearchQuery("");
      setSearchResults([]);
      setAddStockOpen(false);
      fetchWatchlist();
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to add stock";
      toast.error(errorMessage);
    } finally {
      setAdding(false);
    }
  };

  const handleSelectStock = (stock: StockSearchResult) => {
    setTicker(stock.ticker);
    handleAddStock(stock.ticker);
  };

  const handleRemoveStock = async (item: WatchlistItem) => {
    if (!confirm(`Remove ${item.ticker} from watchlist?`)) return;

    try {
      await api.removeStockFromWatchlist(watchlistId, item.ticker);
      toast.success(`Removed ${item.ticker}`);
      fetchWatchlist();
    } catch (error) {
      toast.error("Failed to remove stock");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading watchlist...</p>
      </div>
    );
  }

  if (!watchlist) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/watchlist">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">{watchlist.name}</h1>
            <p className="text-muted-foreground">
              {watchlist.items.length} stocks
            </p>
          </div>
        </div>
        <Dialog open={addStockOpen} onOpenChange={setAddStockOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Stock
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Add Stock</DialogTitle>
              <DialogDescription>
                Search for a stock by ticker or company name
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Search Stocks</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by ticker or company name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
                    className="pl-9"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && searchQuery.trim()) {
                        handleAddStock(searchQuery.trim());
                      }
                    }}
                  />
                  {searching && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                </div>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="border rounded-md max-h-64 overflow-y-auto">
                  {searchResults.map((stock) => (
                    <div
                      key={stock.ticker}
                      className="flex items-center justify-between p-3 hover:bg-muted cursor-pointer border-b last:border-b-0"
                      onClick={() => handleSelectStock(stock)}
                    >
                      <div>
                        <div className="font-medium">{stock.ticker}</div>
                        <div className="text-sm text-muted-foreground truncate max-w-[250px]">
                          {stock.name || "Unknown"}
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" disabled={adding}>
                        {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {searchQuery.length >= 1 && !searching && searchResults.length === 0 && (
                <div className="text-center py-4 text-muted-foreground">
                  No stocks found. Try a different search term or enter the ticker directly.
                </div>
              )}

              {searchQuery.length < 1 && (
                <div className="text-center py-4 text-muted-foreground text-sm">
                  Type to search for stocks (e.g., AAPL, NVDA, Microsoft)
                </div>
              )}
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button variant="outline" onClick={() => {
                setAddStockOpen(false);
                setSearchQuery("");
                setSearchResults([]);
              }}>
                Cancel
              </Button>
              {searchQuery.trim() && (
                <Button onClick={() => handleAddStock(searchQuery.trim())} disabled={adding}>
                  {adding ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>Add &quot;{searchQuery.trim()}&quot;</>
                  )}
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stocks Grid */}
      {watchlist.items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">
              No stocks in this watchlist yet
            </p>
            <Button onClick={() => setAddStockOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Stock
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {watchlist.items.map((item) => (
            <Card key={item.id} className="group relative">
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleRemoveStock(item)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>

              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-xl">{item.ticker}</CardTitle>
                  {item.stock?.sector && (
                    <Badge variant="secondary" className="text-xs">
                      {item.stock.sector}
                    </Badge>
                  )}
                </div>
                {item.stock?.company_name && (
                  <p className="text-sm text-muted-foreground">
                    {item.stock.company_name}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  {item.stock?.exchange && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Building2 className="h-3 w-3" />
                      <span>{item.stock.exchange}</span>
                    </div>
                  )}
                  {item.stock?.market_cap && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <TrendingUp className="h-3 w-3" />
                      <span>
                        Market Cap: $
                        {item.stock.market_cap >= 1000000
                          ? `${(item.stock.market_cap / 1000000).toFixed(2)}T`
                          : item.stock.market_cap >= 1000
                          ? `${(item.stock.market_cap / 1000).toFixed(2)}B`
                          : `${item.stock.market_cap.toFixed(0)}M`}
                      </span>
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground">
                    Added {new Date(item.added_at).toLocaleDateString()}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* News Section */}
      {watchlist.items.length > 0 && (
        <>
          <Separator />
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Latest News</h2>
              <Button variant="outline" size="sm" onClick={fetchNews} disabled={loadingNews}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loadingNews ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>

            {loadingNews ? (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  Loading news...
                </CardContent>
              </Card>
            ) : news.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No recent news for your watchlist stocks
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {news.map((item) => (
                  <Card key={item.id}>
                    <CardContent className="py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline">{item.ticker}</Badge>
                            {item.sentiment && (
                              <Badge
                                variant={
                                  item.sentiment === "bullish"
                                    ? "default"
                                    : item.sentiment === "bearish"
                                    ? "destructive"
                                    : "secondary"
                                }
                              >
                                {item.sentiment}
                              </Badge>
                            )}
                            <span className="text-xs text-muted-foreground">
                              {item.source}
                            </span>
                          </div>
                          <h3 className="font-medium line-clamp-2">{item.headline}</h3>
                          {item.summary && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                              {item.summary}
                            </p>
                          )}
                          <p className="text-xs text-muted-foreground mt-2">
                            {new Date(item.published_at).toLocaleString()}
                          </p>
                        </div>
                        {item.url && (
                          <a href={item.url} target="_blank" rel="noopener noreferrer">
                            <Button variant="ghost" size="icon">
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </a>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
