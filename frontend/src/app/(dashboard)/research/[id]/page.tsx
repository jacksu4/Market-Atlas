"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { ResearchTask } from "@/types";
import { ArrowLeft, CheckCircle, Clock, AlertCircle, XCircle, PlayCircle, Loader2, TrendingUp, Building2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function ResearchTaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;
  const [task, setTask] = useState<ResearchTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTask = async () => {
    try {
      const data = await api.getResearchTask(taskId);
      setTask(data);
      setError(null);
    } catch (err) {
      setError("Failed to load research task");
      toast.error("Failed to load research task");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTask();

    // Poll for updates if task is running
    const interval = setInterval(() => {
      if (task?.status === "running" || task?.status === "queued") {
        fetchTask();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [taskId, task?.status]);

  const handleCancel = async () => {
    try {
      await api.cancelResearchTask(taskId);
      toast.success("Task cancelled");
      fetchTask();
    } catch (err) {
      toast.error("Failed to cancel task");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "running":
        return <PlayCircle className="h-5 w-5 text-blue-500" />;
      case "failed":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case "cancelled":
        return <XCircle className="h-5 w-5 text-gray-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variant =
      status === "completed"
        ? "default"
        : status === "running"
        ? "secondary"
        : status === "failed"
        ? "destructive"
        : "outline";
    return <Badge variant={variant}>{status}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="space-y-4">
        <Link href="/research">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Research
          </Button>
        </Link>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{error || "Task not found"}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <Link href="/research">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Research
          </Button>
        </Link>
        {(task.status === "running" || task.status === "queued") && (
          <Button variant="outline" onClick={handleCancel}>
            Cancel Task
          </Button>
        )}
      </div>

      {/* Task Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                {getStatusIcon(task.status)}
                <CardTitle>{task.title}</CardTitle>
              </div>
              <CardDescription className="flex items-center gap-2">
                <span className="capitalize">{task.task_type.replace("_", " ")}</span>
                <span>•</span>
                <span>{new Date(task.created_at).toLocaleString()}</span>
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {task.status === "running" && (
                <Badge variant="secondary">{task.progress}%</Badge>
              )}
              {getStatusBadge(task.status)}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {task.description && (
            <p className="text-sm text-muted-foreground mb-4">{task.description}</p>
          )}

          {/* Progress Bar for Running Tasks */}
          {task.status === "running" && (
            <div className="space-y-2">
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-500"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Processing... This may take several minutes.
              </p>
            </div>
          )}

          {/* Error Message */}
          {task.status === "failed" && task.error_message && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
              <p className="text-sm text-destructive font-medium">Error:</p>
              <p className="text-sm text-destructive">{task.error_message}</p>
            </div>
          )}

          {/* Queued Status */}
          {task.status === "queued" && (
            <div className="rounded-lg border bg-muted/50 p-4 text-center">
              <Clock className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Task is queued and will start shortly...
              </p>
            </div>
          )}

          {/* Task Parameters */}
          <div className="mt-4 pt-4 border-t">
            <h4 className="text-sm font-medium mb-2">Parameters:</h4>
            <div className="text-xs text-muted-foreground space-y-1">
              {task.task_type === "discovery" && task.parameters.theme && (
                <p>
                  <span className="font-medium">Theme:</span> {task.parameters.theme}
                </p>
              )}
              {task.task_type === "deep_dive" && task.parameters.ticker && (
                <p>
                  <span className="font-medium">Ticker:</span> {task.parameters.ticker}
                </p>
              )}
              {task.parameters.additional_criteria && (
                <p>
                  <span className="font-medium">Criteria:</span>{" "}
                  {task.parameters.additional_criteria}
                </p>
              )}
            </div>
          </div>

          {/* Timestamps */}
          <div className="mt-4 pt-4 border-t text-xs text-muted-foreground space-y-1">
            <p>Created: {new Date(task.created_at).toLocaleString()}</p>
            {task.started_at && (
              <p>Started: {new Date(task.started_at).toLocaleString()}</p>
            )}
            {task.completed_at && (
              <p>Completed: {new Date(task.completed_at).toLocaleString()}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {task.status === "completed" && task.results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Research Results
            </CardTitle>
            <CardDescription>
              {task.task_type === "discovery"
                ? "Discovered stocks matching your criteria"
                : "Comprehensive analysis results"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Discovery Results */}
            {task.task_type === "discovery" && task.results.stocks && (
              <div className="space-y-4">
                {task.results.stocks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    No stocks found matching the criteria
                  </p>
                ) : (
                  <div className="grid gap-4">
                    {task.results.stocks.map((stock: any, idx: number) => (
                      <Card key={idx}>
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="text-lg flex items-center gap-2">
                                <Building2 className="h-4 w-4" />
                                {stock.ticker}
                              </CardTitle>
                              <CardDescription>{stock.company_name}</CardDescription>
                            </div>
                            {stock.score && (
                              <Badge variant="secondary">
                                Score: {stock.score}/10
                              </Badge>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-muted-foreground mb-3">
                            {stock.rationale}
                          </p>
                          {stock.key_points && stock.key_points.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium mb-1">Key Points:</p>
                              <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
                                {stock.key_points.map((point: string, i: number) => (
                                  <li key={i}>{point}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
                {task.results.analysis_summary && (
                  <Card className="mt-4 bg-muted/50">
                    <CardHeader>
                      <CardTitle className="text-base">Analysis Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {task.results.analysis_summary}
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Deep Dive Results */}
            {task.task_type === "deep_dive" && task.results.analysis && (
              <div className="prose prose-sm max-w-none">
                <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {task.results.analysis}
                </div>
              </div>
            )}

            {/* Generic Results Fallback */}
            {!task.results.stocks && !task.results.analysis && (
              <div className="text-sm text-muted-foreground">
                <pre className="whitespace-pre-wrap bg-muted p-4 rounded-lg overflow-x-auto">
                  {JSON.stringify(task.results, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
