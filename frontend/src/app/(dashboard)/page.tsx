"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { Watchlist, News, ResearchTask } from "@/types";
import { ListChecks, FileText, TrendingUp, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [recentNews, setRecentNews] = useState<News[]>([]);
  const [activeTasks, setActiveTasks] = useState<ResearchTask[]>([]);

  useEffect(() => {
    // Fetch watchlists
    api.getWatchlists().then(setWatchlists).catch(console.error);

    // Fetch recent research tasks
    api.getResearchTasks({ limit: 5 }).then(setActiveTasks).catch(console.error);
  }, []);

  const totalStocks = watchlists.reduce((acc, w) => acc + w.items.length, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back to Market Atlas</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Watchlists</CardTitle>
            <ListChecks className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{watchlists.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Tracked Stocks</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStocks}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Research</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {activeTasks.filter((t) => t.status === "running").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Alerts</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>
      </div>

      {/* Watchlists and Research */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Watchlists */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Your Watchlists</CardTitle>
            <Link href="/watchlist" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {watchlists.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No watchlists yet.{" "}
                <Link href="/watchlist" className="text-primary hover:underline">
                  Create one
                </Link>
              </p>
            ) : (
              <div className="space-y-3">
                {watchlists.slice(0, 3).map((watchlist) => (
                  <Link
                    key={watchlist.id}
                    href={`/watchlist/${watchlist.id}`}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted transition-colors"
                  >
                    <div>
                      <p className="font-medium">{watchlist.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {watchlist.items.length} stocks
                      </p>
                    </div>
                    <div className="flex gap-1">
                      {watchlist.items.slice(0, 3).map((item) => (
                        <Badge key={item.id} variant="secondary">
                          {item.ticker}
                        </Badge>
                      ))}
                      {watchlist.items.length > 3 && (
                        <Badge variant="outline">+{watchlist.items.length - 3}</Badge>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Research Tasks */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Research</CardTitle>
            <Link href="/research" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {activeTasks.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No research tasks yet.{" "}
                <Link href="/discover" className="text-primary hover:underline">
                  Start a discovery
                </Link>
              </p>
            ) : (
              <div className="space-y-3">
                {activeTasks.slice(0, 5).map((task) => (
                  <Link
                    key={task.id}
                    href={`/research/${task.id}`}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted transition-colors"
                  >
                    <div>
                      <p className="font-medium">{task.title}</p>
                      <p className="text-sm text-muted-foreground capitalize">
                        {task.task_type.replace("_", " ")}
                      </p>
                    </div>
                    <Badge
                      variant={
                        task.status === "completed"
                          ? "default"
                          : task.status === "running"
                          ? "secondary"
                          : task.status === "failed"
                          ? "destructive"
                          : "outline"
                      }
                    >
                      {task.status}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
