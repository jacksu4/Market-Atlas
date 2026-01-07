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
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight gradient-text">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Welcome back to Market Atlas</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Watchlists</CardTitle>
            <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <ListChecks className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{watchlists.length}</div>
            <div className="h-1 w-12 bg-gradient-to-r from-primary/50 to-transparent rounded-full mt-2"></div>
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tracked Stocks</CardTitle>
            <div className="p-2 rounded-lg bg-accent/10 group-hover:bg-accent/20 transition-colors">
              <TrendingUp className="h-4 w-4 text-accent" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalStocks}</div>
            <div className="h-1 w-12 bg-gradient-to-r from-accent/50 to-transparent rounded-full mt-2"></div>
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Research</CardTitle>
            <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <FileText className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {activeTasks.filter((t) => t.status === "running").length}
            </div>
            <div className="h-1 w-12 bg-gradient-to-r from-primary/50 to-transparent rounded-full mt-2"></div>
          </CardContent>
        </Card>

        <Card className="border-border/40 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Alerts</CardTitle>
            <div className="p-2 rounded-lg bg-muted/10 group-hover:bg-muted/20 transition-colors">
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">0</div>
            <div className="h-1 w-12 bg-gradient-to-r from-muted-foreground/30 to-transparent rounded-full mt-2"></div>
          </CardContent>
        </Card>
      </div>

      {/* Watchlists and Research */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Watchlists */}
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-5 w-5 text-primary" />
              Your Watchlists
            </CardTitle>
            <Link href="/watchlist" className="text-sm text-primary hover:text-primary/80 transition-colors font-medium">
              View all →
            </Link>
          </CardHeader>
          <CardContent>
            {watchlists.length === 0 ? (
              <div className="text-center py-8 rounded-lg border border-dashed border-border/40">
                <p className="text-muted-foreground text-sm">
                  No watchlists yet.{" "}
                  <Link href="/watchlist" className="text-primary hover:underline font-medium">
                    Create one
                  </Link>
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {watchlists.slice(0, 3).map((watchlist) => (
                  <Link
                    key={watchlist.id}
                    href={`/watchlist/${watchlist.id}`}
                    className="flex items-center justify-between rounded-xl border border-border/40 p-4 hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 group"
                  >
                    <div>
                      <p className="font-semibold group-hover:text-primary transition-colors">{watchlist.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {watchlist.items.length} stocks
                      </p>
                    </div>
                    <div className="flex gap-1.5">
                      {watchlist.items.slice(0, 3).map((item) => (
                        <Badge key={item.id} variant="secondary" className="bg-primary/10 text-primary border-primary/20">
                          {item.ticker}
                        </Badge>
                      ))}
                      {watchlist.items.length > 3 && (
                        <Badge variant="outline" className="border-border/40">+{watchlist.items.length - 3}</Badge>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Research Tasks */}
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Recent Research
            </CardTitle>
            <Link href="/research" className="text-sm text-primary hover:text-primary/80 transition-colors font-medium">
              View all →
            </Link>
          </CardHeader>
          <CardContent>
            {activeTasks.length === 0 ? (
              <div className="text-center py-8 rounded-lg border border-dashed border-border/40">
                <p className="text-muted-foreground text-sm">
                  No research tasks yet.{" "}
                  <Link href="/discover" className="text-primary hover:underline font-medium">
                    Start a discovery
                  </Link>
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {activeTasks.slice(0, 5).map((task) => (
                  <Link
                    key={task.id}
                    href={`/research/${task.id}`}
                    className="flex items-center justify-between rounded-xl border border-border/40 p-4 hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 group"
                  >
                    <div className="flex-1">
                      <p className="font-semibold group-hover:text-primary transition-colors">{task.title}</p>
                      <p className="text-xs text-muted-foreground capitalize mt-0.5">
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
                      className={
                        task.status === "running"
                          ? "bg-primary/10 text-primary border-primary/20"
                          : ""
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
