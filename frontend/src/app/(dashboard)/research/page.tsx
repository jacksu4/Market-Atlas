"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { ResearchTask } from "@/types";
import { RefreshCw, XCircle, CheckCircle, Clock, AlertCircle, PlayCircle } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function ResearchPage() {
  const [tasks, setTasks] = useState<ResearchTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  const fetchTasks = async () => {
    try {
      const data = await api.getResearchTasks({ limit: 50 });
      setTasks(data);
    } catch (error) {
      toast.error("Failed to load research tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    // Poll for updates
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleCancelTask = async (id: string) => {
    try {
      await api.cancelResearchTask(id);
      toast.success("Task cancelled");
      fetchTasks();
    } catch (error) {
      toast.error("Failed to cancel task");
    }
  };

  const filteredTasks = tasks.filter((task) => {
    if (filter === "all") return true;
    return task.status === filter;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "running":
        return <PlayCircle className="h-4 w-4 text-blue-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "cancelled":
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading research tasks...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Research Tasks</h1>
          <p className="text-muted-foreground">
            View and manage your research tasks
          </p>
        </div>
        <Button variant="outline" onClick={fetchTasks}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="all" onValueChange={setFilter}>
        <TabsList>
          <TabsTrigger value="all">All ({tasks.length})</TabsTrigger>
          <TabsTrigger value="running">
            Running ({tasks.filter((t) => t.status === "running").length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completed ({tasks.filter((t) => t.status === "completed").length})
          </TabsTrigger>
          <TabsTrigger value="failed">
            Failed ({tasks.filter((t) => t.status === "failed").length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={filter} className="mt-4">
          {filteredTasks.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <p className="text-muted-foreground mb-4">
                  No research tasks found
                </p>
                <Link href="/discover">
                  <Button>Start a Discovery</Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredTasks.map((task) => (
                <Card key={task.id}>
                  <CardHeader className="flex flex-row items-start justify-between pb-2">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        {getStatusIcon(task.status)}
                        {task.title}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground capitalize">
                        {task.task_type.replace("_", " ")} &bull;{" "}
                        {new Date(task.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {task.status === "running" && (
                        <Badge variant="secondary">{task.progress}%</Badge>
                      )}
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
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-muted-foreground">
                        {task.status === "running" && (
                          <span>Processing... This may take a few minutes.</span>
                        )}
                        {task.status === "completed" && task.completed_at && (
                          <span>
                            Completed{" "}
                            {new Date(task.completed_at).toLocaleString()}
                          </span>
                        )}
                        {task.status === "failed" && task.error_message && (
                          <span className="text-destructive">
                            {task.error_message}
                          </span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {(task.status === "running" || task.status === "queued") && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCancelTask(task.id)}
                          >
                            Cancel
                          </Button>
                        )}
                        {task.status === "completed" && (
                          <Link href={`/research/${task.id}`}>
                            <Button size="sm">View Results</Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
