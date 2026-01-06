"use client";

import { useEffect, useState } from "react";
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
import { api } from "@/lib/api";
import { Watchlist } from "@/types";
import { Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function WatchlistPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchWatchlists = async () => {
    try {
      const data = await api.getWatchlists();
      setWatchlists(data);
    } catch (error) {
      toast.error("Failed to load watchlists");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlists();
  }, []);

  const handleCreateWatchlist = async () => {
    if (!newWatchlistName.trim()) return;

    setCreating(true);
    try {
      await api.createWatchlist(newWatchlistName.trim());
      toast.success("Watchlist created");
      setNewWatchlistName("");
      setCreateDialogOpen(false);
      fetchWatchlists();
    } catch (error) {
      toast.error("Failed to create watchlist");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteWatchlist = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;

    try {
      await api.deleteWatchlist(id);
      toast.success("Watchlist deleted");
      fetchWatchlists();
    } catch (error) {
      toast.error("Failed to delete watchlist");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading watchlists...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Watchlists</h1>
          <p className="text-muted-foreground">
            Track and monitor your stocks
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Watchlist
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Watchlist</DialogTitle>
              <DialogDescription>
                Create a new watchlist to track stocks
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., AI Tech Stocks"
                  value={newWatchlistName}
                  onChange={(e) => setNewWatchlistName(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateWatchlist} disabled={creating}>
                {creating ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {watchlists.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-4">
              You don&apos;t have any watchlists yet
            </p>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Watchlist
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {watchlists.map((watchlist) => (
            <Card key={watchlist.id} className="group relative">
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleDeleteWatchlist(watchlist.id, watchlist.name)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>

              <Link href={`/watchlist/${watchlist.id}`}>
                <CardHeader>
                  <CardTitle className="text-lg">{watchlist.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {watchlist.items.length} stocks
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1">
                    {watchlist.items.slice(0, 5).map((item) => (
                      <Badge key={item.id} variant="secondary">
                        {item.ticker}
                      </Badge>
                    ))}
                    {watchlist.items.length > 5 && (
                      <Badge variant="outline">
                        +{watchlist.items.length - 5} more
                      </Badge>
                    )}
                    {watchlist.items.length === 0 && (
                      <span className="text-sm text-muted-foreground">
                        No stocks added yet
                      </span>
                    )}
                  </div>
                </CardContent>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
