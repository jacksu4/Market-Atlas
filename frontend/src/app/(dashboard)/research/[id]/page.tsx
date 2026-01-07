"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { ResearchTask } from "@/types";
import {
  ArrowLeft, CheckCircle, Clock, AlertCircle, XCircle, PlayCircle,
  TrendingUp, TrendingDown, Building2, Target, Shield, AlertTriangle,
  BarChart3, PieChart, FileText, ExternalLink, ChevronDown, ChevronUp,
  Star, Zap, DollarSign, Percent, Activity, Users, BookOpen, Info
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// Types for the comprehensive research report
interface ScoreBreakdown {
  theme_alignment: number;
  financial_health: number;
  growth_potential: number;
  valuation: number;
}

interface Catalyst {
  catalyst: string;
  timeline: string;
  impact: string;
}

interface Strength {
  point: string;
  detail: string;
}

interface Risk {
  risk: string;
  severity: string;
  mitigation: string;
}

interface FinancialMetrics {
  revenue_growth_yoy: string;
  gross_margin: string;
  operating_margin: string;
  net_margin: string;
  pe_ratio: string;
  ps_ratio: string;
  debt_to_equity: string;
  free_cash_flow: string;
  roe: string;
}

interface CompetitivePosition {
  market_share: string;
  key_competitors: string[];
  competitive_moat: string;
}

interface Stock {
  ticker: string;
  company_name: string;
  sector: string;
  market_cap: string;
  overall_score: number;
  score_breakdown: ScoreBreakdown;
  recommendation: string;
  price_target_upside: string;
  investment_thesis: string;
  key_catalysts: Catalyst[];
  strengths: Strength[];
  risks: Risk[];
  financial_metrics: FinancialMetrics;
  competitive_position: CompetitivePosition;
  recent_developments: string[];
}

interface RiskItem {
  risk: string;
  probability: string;
  impact: string;
}

interface ResearchResults {
  report_metadata?: {
    generated_at: string;
    theme: string;
    time_horizon: string;
    risk_profile: string;
    analyst_confidence: string;
  };
  executive_summary?: {
    overview: string;
    key_conclusion: string;
    top_picks: string[];
    sector_outlook: string;
    market_conditions: string;
  };
  scoring_methodology?: {
    description: string;
    dimensions: { name: string; weight: number; description: string }[];
  };
  stocks?: Stock[];
  sector_analysis?: {
    industry_overview: string;
    market_size: string;
    growth_drivers: string[];
    headwinds: string[];
    competitive_landscape: string;
  };
  risk_matrix?: {
    macro_risks: RiskItem[];
    sector_risks: RiskItem[];
    execution_risks: RiskItem[];
  };
  data_sources?: string[];
  disclaimers?: string;
  // Legacy format support
  candidates?: any[];
  methodology?: string;
  market_overview?: string;
}

export default function ResearchTaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;
  const [task, setTask] = useState<ResearchTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedStocks, setExpandedStocks] = useState<Set<string>>(new Set());

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

  const toggleStockExpand = (ticker: string) => {
    setExpandedStocks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(ticker)) {
        newSet.delete(ticker);
      } else {
        newSet.add(ticker);
      }
      return newSet;
    });
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
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></div>
          <p className="text-muted-foreground text-sm">Loading research task...</p>
        </div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="space-y-4">
        <Link href="/research">
          <Button variant="outline" className="border-border/40 hover:border-primary/50 hover:bg-primary/5">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Research
          </Button>
        </Link>
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="p-4 rounded-full bg-destructive/10 mb-4">
              <AlertCircle className="h-10 w-10 text-destructive" />
            </div>
            <p className="text-muted-foreground text-lg">{error || "Task not found"}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const results = task.results as ResearchResults;

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/research">
          <Button variant="outline" className="border-border/40 hover:border-primary/50 hover:bg-primary/5">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回研究列表
          </Button>
        </Link>
        {(task.status === "running" || task.status === "queued") && (
          <Button variant="outline" onClick={handleCancel} className="border-destructive/40 hover:border-destructive hover:bg-destructive/10 text-destructive">
            取消任务
          </Button>
        )}
      </div>

      {/* Task Status Card */}
      <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
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
                <span>{new Date(task.created_at).toLocaleString("zh-CN")}</span>
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
          {/* Progress Bar */}
          {task.status === "running" && (
            <div className="space-y-2">
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-500"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground text-center">
                正在生成研究报告... 这可能需要几分钟时间。
              </p>
            </div>
          )}

          {/* Error Message */}
          {task.status === "failed" && task.error_message && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
              <p className="text-sm text-destructive font-medium">错误：</p>
              <p className="text-sm text-destructive">{task.error_message}</p>
            </div>
          )}

          {/* Queued Status */}
          {task.status === "queued" && (
            <div className="rounded-lg border bg-muted/50 p-4 text-center">
              <Clock className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                任务已排队，即将开始...
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Research Report */}
      {task.status === "completed" && results && (
        <>
          {/* Check report type and render appropriate component */}
          {task.task_type === "deep_dive" && results.company_overview ? (
            <DeepDiveReport results={results as any} />
          ) : results.executive_summary ? (
            <ComprehensiveReport
              results={results}
              expandedStocks={expandedStocks}
              toggleStockExpand={toggleStockExpand}
            />
          ) : results.candidates ? (
            <LegacyReport results={results} />
          ) : (
            <FallbackReport results={results} />
          )}
        </>
      )}
    </div>
  );
}

// Comprehensive Report Component (New Format)
function ComprehensiveReport({
  results,
  expandedStocks,
  toggleStockExpand
}: {
  results: ResearchResults;
  expandedStocks: Set<string>;
  toggleStockExpand: (ticker: string) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Report Metadata */}
      {results.report_metadata && (
        <div className="flex flex-wrap gap-2 items-center text-sm text-muted-foreground">
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            {results.report_metadata.generated_at}
          </Badge>
          <Badge variant="outline" className="gap-1">
            <Target className="h-3 w-3" />
            {results.report_metadata.time_horizon === "short" ? "短期" :
             results.report_metadata.time_horizon === "medium" ? "中期" : "长期"}
          </Badge>
          <Badge variant="outline" className="gap-1">
            <Shield className="h-3 w-3" />
            {results.report_metadata.risk_profile === "conservative" ? "保守型" :
             results.report_metadata.risk_profile === "moderate" ? "稳健型" : "激进型"}
          </Badge>
          <Badge
            variant={results.report_metadata.analyst_confidence === "high" ? "default" : "secondary"}
            className="gap-1"
          >
            分析师信心: {results.report_metadata.analyst_confidence === "high" ? "高" :
                        results.report_metadata.analyst_confidence === "medium" ? "中" : "低"}
          </Badge>
        </div>
      )}

      {/* Executive Summary */}
      {results.executive_summary && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 rounded-lg bg-primary/10">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              执行摘要
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {results.executive_summary.overview}
            </p>

            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <p className="font-medium text-primary">
                {results.executive_summary.key_conclusion}
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">首选标的</p>
                <div className="flex flex-wrap gap-1">
                  {results.executive_summary.top_picks.map((ticker) => (
                    <Badge key={ticker} variant="secondary" className="font-mono">
                      {ticker}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">行业展望</p>
                <Badge
                  variant={
                    results.executive_summary.sector_outlook === "bullish" ? "default" :
                    results.executive_summary.sector_outlook === "bearish" ? "destructive" : "secondary"
                  }
                >
                  {results.executive_summary.sector_outlook === "bullish" ? "看涨" :
                   results.executive_summary.sector_outlook === "bearish" ? "看跌" : "中性"}
                </Badge>
              </div>
            </div>

            <div className="pt-4 border-t">
              <p className="text-xs text-muted-foreground mb-2">市场环境</p>
              <p className="text-sm text-muted-foreground">
                {results.executive_summary.market_conditions}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scoring Methodology */}
      {results.scoring_methodology && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <BarChart3 className="h-5 w-5 text-accent" />
              </div>
              评分方法论
            </CardTitle>
            <CardDescription>{results.scoring_methodology.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {results.scoring_methodology.dimensions.map((dim) => (
                <div key={dim.name} className="p-3 rounded-lg border border-border/40 bg-muted/30">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm">{dim.name}</span>
                    <Badge variant="outline">{dim.weight}分</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{dim.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stock Recommendations */}
      {results.stocks && results.stocks.length > 0 && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 rounded-lg bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              股票推荐 ({results.stocks.length})
            </CardTitle>
            <CardDescription>
              根据主题相关性、财务健康度、增长潜力和估值进行综合评估
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {results.stocks.map((stock, idx) => (
              <StockCard
                key={stock.ticker}
                stock={stock}
                rank={idx + 1}
                isExpanded={expandedStocks.has(stock.ticker)}
                onToggle={() => toggleStockExpand(stock.ticker)}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Sector Analysis */}
      {results.sector_analysis && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <PieChart className="h-5 w-5 text-accent" />
              </div>
              行业分析
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {results.sector_analysis.industry_overview}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border border-border/40 bg-muted/30">
                <p className="text-xs text-muted-foreground mb-2">市场规模</p>
                <p className="font-medium">{results.sector_analysis.market_size}</p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 bg-muted/30">
                <p className="text-xs text-muted-foreground mb-2">竞争格局</p>
                <p className="text-sm">{results.sector_analysis.competitive_landscape}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium mb-2 flex items-center gap-1">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  增长驱动因素
                </p>
                <ul className="space-y-1">
                  {results.sector_analysis.growth_drivers.map((driver, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-green-500">•</span>
                      {driver}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-sm font-medium mb-2 flex items-center gap-1">
                  <TrendingDown className="h-4 w-4 text-red-500" />
                  逆风因素
                </p>
                <ul className="space-y-1">
                  {results.sector_analysis.headwinds.map((headwind, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-red-500">•</span>
                      {headwind}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risk Matrix */}
      {results.risk_matrix && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-destructive/10">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              风险矩阵
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <RiskCategory title="宏观风险" risks={results.risk_matrix.macro_risks} />
              <RiskCategory title="行业风险" risks={results.risk_matrix.sector_risks} />
              <RiskCategory title="执行风险" risks={results.risk_matrix.execution_risks} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Sources & Disclaimers */}
      <Card className="border-border/40 bg-muted/30">
        <CardContent className="pt-6">
          <div className="space-y-4">
            {results.data_sources && (
              <div>
                <p className="text-xs font-medium mb-2 flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  数据来源
                </p>
                <div className="flex flex-wrap gap-2">
                  {results.data_sources.map((source, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {results.disclaimers && (
              <div className="pt-4 border-t">
                <p className="text-xs text-muted-foreground flex items-start gap-1">
                  <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  {results.disclaimers}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Stock Card Component
function StockCard({
  stock,
  rank,
  isExpanded,
  onToggle
}: {
  stock: Stock;
  rank: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const getRecommendationColor = (rec: string) => {
    switch (rec.toLowerCase()) {
      case "strong buy":
        return "bg-green-500/10 text-green-500 border-green-500/20";
      case "buy":
        return "bg-green-400/10 text-green-400 border-green-400/20";
      case "hold":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
      case "sell":
        return "bg-red-500/10 text-red-500 border-red-500/20";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className="border border-border/40 rounded-lg bg-muted/30 overflow-hidden">
      {/* Stock Header - Always Visible */}
      <div
        className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-sm">
              #{rank}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg font-mono">{stock.ticker}</span>
                <Badge variant="outline" className="text-xs">{stock.sector}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">{stock.company_name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className={cn("text-2xl font-bold", getScoreColor(stock.overall_score))}>
                {stock.overall_score}
              </div>
              <p className="text-xs text-muted-foreground">综合评分</p>
            </div>
            <Badge className={cn("border", getRecommendationColor(stock.recommendation))}>
              {stock.recommendation}
            </Badge>
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-xs text-muted-foreground">市值</p>
            <p className="font-medium">{stock.market_cap}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">上涨空间</p>
            <p className="font-medium text-green-500">{stock.price_target_upside}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">主题契合度</p>
            <p className="font-medium">{stock.score_breakdown.theme_alignment}/25</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">财务健康</p>
            <p className="font-medium">{stock.score_breakdown.financial_health}/25</p>
          </div>
        </div>

        {/* Investment Thesis */}
        <p className="mt-4 text-sm text-muted-foreground">
          {stock.investment_thesis}
        </p>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 border-t border-border/40 space-y-6">
          {/* Score Breakdown Visual */}
          <div>
            <p className="text-sm font-medium mb-3">评分明细</p>
            <div className="space-y-2">
              <ScoreBar label="主题契合度" score={stock.score_breakdown.theme_alignment} max={25} />
              <ScoreBar label="财务健康度" score={stock.score_breakdown.financial_health} max={25} />
              <ScoreBar label="增长潜力" score={stock.score_breakdown.growth_potential} max={25} />
              <ScoreBar label="估值评分" score={stock.score_breakdown.valuation} max={25} />
            </div>
          </div>

          {/* Financial Metrics */}
          {stock.financial_metrics && (
            <div>
              <p className="text-sm font-medium mb-3 flex items-center gap-1">
                <BarChart3 className="h-4 w-4" />
                财务指标
              </p>
              <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
                <MetricCard label="收入增长(YoY)" value={stock.financial_metrics.revenue_growth_yoy} />
                <MetricCard label="毛利率" value={stock.financial_metrics.gross_margin} />
                <MetricCard label="营业利润率" value={stock.financial_metrics.operating_margin} />
                <MetricCard label="净利率" value={stock.financial_metrics.net_margin} />
                <MetricCard label="P/E" value={stock.financial_metrics.pe_ratio} />
                <MetricCard label="P/S" value={stock.financial_metrics.ps_ratio} />
                <MetricCard label="D/E" value={stock.financial_metrics.debt_to_equity} />
                <MetricCard label="自由现金流" value={stock.financial_metrics.free_cash_flow} />
                <MetricCard label="ROE" value={stock.financial_metrics.roe} />
              </div>
            </div>
          )}

          {/* Key Catalysts */}
          {stock.key_catalysts && stock.key_catalysts.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-3 flex items-center gap-1">
                <Zap className="h-4 w-4" />
                关键催化剂
              </p>
              <div className="space-y-2">
                {stock.key_catalysts.map((catalyst, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 rounded bg-muted/50">
                    <Badge
                      variant={catalyst.impact === "high" ? "default" : "outline"}
                      className="text-xs mt-0.5"
                    >
                      {catalyst.timeline}
                    </Badge>
                    <div className="flex-1">
                      <p className="text-sm">{catalyst.catalyst}</p>
                      <p className="text-xs text-muted-foreground">
                        影响: {catalyst.impact === "high" ? "高" : catalyst.impact === "medium" ? "中" : "低"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strengths & Risks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            {stock.strengths && stock.strengths.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-3 flex items-center gap-1 text-green-500">
                  <Star className="h-4 w-4" />
                  核心优势
                </p>
                <div className="space-y-2">
                  {stock.strengths.map((strength, i) => (
                    <div key={i} className="p-2 rounded bg-green-500/5 border border-green-500/20">
                      <p className="text-sm font-medium">{strength.point}</p>
                      <p className="text-xs text-muted-foreground">{strength.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risks */}
            {stock.risks && stock.risks.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-3 flex items-center gap-1 text-red-500">
                  <AlertTriangle className="h-4 w-4" />
                  主要风险
                </p>
                <div className="space-y-2">
                  {stock.risks.map((risk, i) => (
                    <div key={i} className="p-2 rounded bg-red-500/5 border border-red-500/20">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{risk.risk}</p>
                        <Badge
                          variant={risk.severity === "high" ? "destructive" : "outline"}
                          className="text-xs"
                        >
                          {risk.severity === "high" ? "高" : risk.severity === "medium" ? "中" : "低"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        缓解措施: {risk.mitigation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Competitive Position */}
          {stock.competitive_position && (
            <div>
              <p className="text-sm font-medium mb-3 flex items-center gap-1">
                <Users className="h-4 w-4" />
                竞争地位
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3 rounded border border-border/40">
                  <p className="text-xs text-muted-foreground">市场份额</p>
                  <p className="font-medium">{stock.competitive_position.market_share}</p>
                </div>
                <div className="p-3 rounded border border-border/40">
                  <p className="text-xs text-muted-foreground">主要竞争对手</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {stock.competitive_position.key_competitors.map((comp, i) => (
                      <Badge key={i} variant="outline" className="text-xs">{comp}</Badge>
                    ))}
                  </div>
                </div>
                <div className="p-3 rounded border border-border/40 md:col-span-1">
                  <p className="text-xs text-muted-foreground">竞争壁垒</p>
                  <p className="text-sm mt-1">{stock.competitive_position.competitive_moat}</p>
                </div>
              </div>
            </div>
          )}

          {/* Recent Developments */}
          {stock.recent_developments && stock.recent_developments.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-3 flex items-center gap-1">
                <Activity className="h-4 w-4" />
                近期动态
              </p>
              <ul className="space-y-1">
                {stock.recent_developments.map((dev, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span className="text-primary">•</span>
                    {dev}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Score Bar Component
function ScoreBar({ label, score, max }: { label: string; score: number; max: number }) {
  const percentage = (score / max) * 100;
  const getColor = () => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-muted-foreground w-24">{label}</span>
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", getColor())} style={{ width: `${percentage}%` }} />
      </div>
      <span className="text-xs font-medium w-12 text-right">{score}/{max}</span>
    </div>
  );
}

// Metric Card Component
function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2 rounded border border-border/40 text-center">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium text-sm">{value}</p>
    </div>
  );
}

// Risk Category Component
function RiskCategory({ title, risks }: { title: string; risks: RiskItem[] }) {
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high":
        return "text-red-500";
      case "medium":
        return "text-yellow-500";
      default:
        return "text-green-500";
    }
  };

  return (
    <div className="p-4 rounded-lg border border-border/40">
      <p className="font-medium text-sm mb-3">{title}</p>
      <div className="space-y-2">
        {risks.map((risk, i) => (
          <div key={i} className="text-sm">
            <p className="text-muted-foreground">{risk.risk}</p>
            <div className="flex gap-2 mt-1">
              <Badge variant="outline" className="text-xs">
                概率: {risk.probability === "high" ? "高" : risk.probability === "medium" ? "中" : "低"}
              </Badge>
              <Badge variant="outline" className={cn("text-xs", getImpactColor(risk.impact))}>
                影响: {risk.impact === "high" ? "高" : risk.impact === "medium" ? "中" : "低"}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Legacy Report Component (for old format)
function LegacyReport({ results }: { results: ResearchResults }) {
  return (
    <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <div className="p-2 rounded-lg bg-primary/10">
            <TrendingUp className="h-5 w-5 text-primary" />
          </div>
          研究结果
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {results.methodology && (
          <div className="p-4 rounded-lg bg-muted/50">
            <p className="text-sm font-medium mb-2">研究方法</p>
            <p className="text-sm text-muted-foreground">{results.methodology}</p>
          </div>
        )}

        {results.market_overview && (
          <div className="p-4 rounded-lg bg-muted/50">
            <p className="text-sm font-medium mb-2">市场概览</p>
            <p className="text-sm text-muted-foreground">{results.market_overview}</p>
          </div>
        )}

        {results.candidates && results.candidates.length > 0 && (
          <div className="space-y-3">
            {results.candidates.map((candidate: any, idx: number) => (
              <Card key={idx} className="border-border/40 bg-muted/30">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        {candidate.ticker}
                      </CardTitle>
                      <CardDescription>{candidate.company_name}</CardDescription>
                    </div>
                    {candidate.confidence_score && (
                      <Badge variant="secondary">
                        信心: {candidate.confidence_score}/100
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">{candidate.theme_fit}</p>
                  {candidate.investment_thesis && (
                    <div>
                      <p className="text-xs font-medium mb-1">投资逻辑</p>
                      <p className="text-sm text-muted-foreground">{candidate.investment_thesis}</p>
                    </div>
                  )}
                  {candidate.risks && candidate.risks.length > 0 && (
                    <div>
                      <p className="text-xs font-medium mb-1">风险</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {candidate.risks.map((risk: string, i: number) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-red-500">•</span>
                            {risk}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Fallback Report Component (for unknown format)
function FallbackReport({ results }: { results: ResearchResults }) {
  return (
    <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <div className="p-2 rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          研究结果
        </CardTitle>
        <CardDescription>
          原始数据格式 - 正在开发更好的展示方式
        </CardDescription>
      </CardHeader>
      <CardContent>
        <pre className="whitespace-pre-wrap bg-muted p-4 rounded-lg overflow-x-auto text-xs">
          {JSON.stringify(results, null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}

// Deep Dive Report Types
interface DeepDiveResults {
  report_metadata?: {
    ticker: string;
    generated_at: string;
    report_type: string;
    analyst_confidence: string;
  };
  company_overview?: {
    name: string;
    description: string;
    sector: string;
    industry: string;
    headquarters: string;
    founded: string;
    employees: string;
    website: string;
  };
  executive_summary?: {
    investment_rating: string;
    price_target: string;
    upside_potential: string;
    key_thesis: string;
    risk_reward: string;
  };
  business_analysis?: {
    business_model: string;
    revenue_streams: { stream: string; percentage: string; growth_trend: string }[];
    competitive_advantages: string[];
    market_position: string;
    key_products_services: string[];
  };
  financial_analysis?: {
    revenue_trend: string;
    profitability: string;
    balance_sheet_health: string;
    cash_flow_quality: string;
    key_metrics: {
      revenue_growth: string;
      gross_margin: string;
      operating_margin: string;
      net_margin: string;
      roe: string;
      debt_to_equity: string;
      current_ratio: string;
      pe_ratio: string;
      ps_ratio: string;
      ev_ebitda: string;
    };
    financial_outlook: string;
  };
  growth_drivers?: { driver: string; impact: string; timeline: string; description: string }[];
  risk_factors?: { risk: string; severity: string; probability: string; mitigation: string }[];
  competitive_landscape?: {
    main_competitors: { name: string; ticker: string; comparison: string }[];
    competitive_position: string;
    barriers_to_entry: string;
    threat_assessment: string;
  };
  valuation_analysis?: {
    current_valuation: string;
    valuation_vs_peers: string;
    valuation_vs_history: string;
    fair_value_estimate: string;
    methodology: string;
    key_assumptions: string[];
  };
  catalysts?: {
    near_term: { catalyst: string; expected_timing: string; potential_impact: string }[];
    long_term: { catalyst: string; expected_timing: string; potential_impact: string }[];
  };
  investment_recommendation?: {
    summary: string;
    ideal_investor_profile: string;
    position_sizing: string;
    entry_strategy: string;
    exit_triggers: string[];
  };
  data_sources?: string[];
  disclaimers?: string;
}

// Deep Dive Report Component
function DeepDiveReport({ results }: { results: DeepDiveResults }) {
  const getRatingColor = (rating: string) => {
    const lower = rating.toLowerCase();
    if (lower.includes("strong buy")) return "bg-green-500 text-white";
    if (lower.includes("buy")) return "bg-green-400 text-white";
    if (lower.includes("hold")) return "bg-yellow-500 text-white";
    if (lower.includes("sell")) return "bg-red-500 text-white";
    return "bg-muted";
  };

  const getImpactBadge = (impact: string) => {
    switch (impact.toLowerCase()) {
      case "high":
        return <Badge className="bg-green-500/10 text-green-500 border-green-500/20">高</Badge>;
      case "medium":
        return <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">中</Badge>;
      default:
        return <Badge className="bg-gray-500/10 text-gray-500 border-gray-500/20">低</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Report Header with Company Overview */}
      {results.company_overview && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Building2 className="h-6 w-6 text-primary" />
                  </div>
                  <span className="font-mono">{results.report_metadata?.ticker}</span>
                  <span className="text-muted-foreground font-normal">|</span>
                  <span>{results.company_overview.name}</span>
                </CardTitle>
                <CardDescription className="mt-2">
                  {results.company_overview.sector} • {results.company_overview.industry}
                </CardDescription>
              </div>
              {results.executive_summary && (
                <Badge className={cn("text-lg px-4 py-2", getRatingColor(results.executive_summary.investment_rating))}>
                  {results.executive_summary.investment_rating}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">{results.company_overview.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
              <div>
                <p className="text-xs text-muted-foreground">总部</p>
                <p className="font-medium">{results.company_overview.headquarters}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">成立年份</p>
                <p className="font-medium">{results.company_overview.founded}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">员工数量</p>
                <p className="font-medium">{results.company_overview.employees}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">官网</p>
                <a href={`https://${results.company_overview.website}`} target="_blank" rel="noopener noreferrer"
                   className="font-medium text-primary hover:underline flex items-center gap-1">
                  {results.company_overview.website}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Executive Summary */}
      {results.executive_summary && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 rounded-lg bg-primary/10">
                <Target className="h-5 w-5 text-primary" />
              </div>
              投资摘要
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <p className="text-primary font-medium">{results.executive_summary.key_thesis}</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">目标价</p>
                <p className="text-2xl font-bold text-primary">{results.executive_summary.price_target}</p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">上涨空间</p>
                <p className="text-2xl font-bold text-green-500">{results.executive_summary.upside_potential}</p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">风险收益比</p>
                <p className="text-lg font-bold">{results.executive_summary.risk_reward}</p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">分析师信心</p>
                <p className="text-lg font-bold">
                  {results.report_metadata?.analyst_confidence === "high" ? "高" :
                   results.report_metadata?.analyst_confidence === "medium" ? "中" : "低"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Business Analysis */}
      {results.business_analysis && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <Activity className="h-5 w-5 text-accent" />
              </div>
              业务分析
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">商业模式</p>
              <p className="text-sm text-muted-foreground">{results.business_analysis.business_model}</p>
            </div>

            {results.business_analysis.revenue_streams && results.business_analysis.revenue_streams.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">收入构成</p>
                <div className="space-y-2">
                  {results.business_analysis.revenue_streams.map((stream, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded bg-muted/50">
                      <span className="text-sm">{stream.stream}</span>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{stream.percentage}</Badge>
                        <Badge variant={stream.growth_trend === "growing" ? "default" :
                                       stream.growth_trend === "declining" ? "destructive" : "secondary"}>
                          {stream.growth_trend === "growing" ? "增长" :
                           stream.growth_trend === "declining" ? "下滑" : "稳定"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium mb-2 text-green-500">竞争优势</p>
                <ul className="space-y-1">
                  {results.business_analysis.competitive_advantages.map((adv, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <Star className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      {adv}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-sm font-medium mb-2">主要产品/服务</p>
                <div className="flex flex-wrap gap-2">
                  {results.business_analysis.key_products_services.map((product, i) => (
                    <Badge key={i} variant="outline">{product}</Badge>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-muted/50">
              <p className="text-xs text-muted-foreground mb-1">市场地位</p>
              <p className="text-sm">{results.business_analysis.market_position}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Financial Analysis */}
      {results.financial_analysis && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <BarChart3 className="h-5 w-5 text-accent" />
              </div>
              财务分析
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">收入趋势</p>
                <p className="text-sm">{results.financial_analysis.revenue_trend}</p>
              </div>
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">盈利能力</p>
                <p className="text-sm">{results.financial_analysis.profitability}</p>
              </div>
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">资产负债表健康度</p>
                <Badge variant={results.financial_analysis.balance_sheet_health === "Strong" ? "default" :
                               results.financial_analysis.balance_sheet_health === "Weak" ? "destructive" : "secondary"}>
                  {results.financial_analysis.balance_sheet_health === "Strong" ? "强健" :
                   results.financial_analysis.balance_sheet_health === "Weak" ? "较弱" : "适中"}
                </Badge>
              </div>
            </div>

            {results.financial_analysis.key_metrics && (
              <div>
                <p className="text-sm font-medium mb-3">核心财务指标</p>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <MetricCard label="收入增长" value={results.financial_analysis.key_metrics.revenue_growth} />
                  <MetricCard label="毛利率" value={results.financial_analysis.key_metrics.gross_margin} />
                  <MetricCard label="营业利润率" value={results.financial_analysis.key_metrics.operating_margin} />
                  <MetricCard label="净利率" value={results.financial_analysis.key_metrics.net_margin} />
                  <MetricCard label="ROE" value={results.financial_analysis.key_metrics.roe} />
                  <MetricCard label="P/E" value={results.financial_analysis.key_metrics.pe_ratio} />
                  <MetricCard label="P/S" value={results.financial_analysis.key_metrics.ps_ratio} />
                  <MetricCard label="EV/EBITDA" value={results.financial_analysis.key_metrics.ev_ebitda} />
                  <MetricCard label="D/E" value={results.financial_analysis.key_metrics.debt_to_equity} />
                  <MetricCard label="流动比率" value={results.financial_analysis.key_metrics.current_ratio} />
                </div>
              </div>
            )}

            <div className="p-3 rounded-lg bg-muted/50">
              <p className="text-xs text-muted-foreground mb-1">财务展望</p>
              <p className="text-sm">{results.financial_analysis.financial_outlook}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Growth Drivers & Risk Factors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Growth Drivers */}
        {results.growth_drivers && results.growth_drivers.length > 0 && (
          <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-green-500">
                <TrendingUp className="h-5 w-5" />
                增长驱动因素
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {results.growth_drivers.map((driver, i) => (
                <div key={i} className="p-3 rounded-lg bg-green-500/5 border border-green-500/20">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm">{driver.driver}</span>
                    {getImpactBadge(driver.impact)}
                  </div>
                  <p className="text-xs text-muted-foreground mb-1">{driver.description}</p>
                  <Badge variant="outline" className="text-xs">
                    {driver.timeline === "near-term" ? "近期" :
                     driver.timeline === "medium-term" ? "中期" : "长期"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Risk Factors */}
        {results.risk_factors && results.risk_factors.length > 0 && (
          <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-red-500">
                <AlertTriangle className="h-5 w-5" />
                风险因素
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {results.risk_factors.map((risk, i) => (
                <div key={i} className="p-3 rounded-lg bg-red-500/5 border border-red-500/20">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm">{risk.risk}</span>
                    <Badge variant={risk.severity === "high" ? "destructive" : "outline"} className="text-xs">
                      {risk.severity === "high" ? "高风险" : risk.severity === "medium" ? "中风险" : "低风险"}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-1">
                    <span className="font-medium">缓解措施：</span>{risk.mitigation}
                  </p>
                  <Badge variant="outline" className="text-xs">
                    发生概率: {risk.probability === "high" ? "高" : risk.probability === "medium" ? "中" : "低"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Competitive Landscape */}
      {results.competitive_landscape && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <Users className="h-5 w-5 text-accent" />
              </div>
              竞争格局
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">竞争地位</p>
                <p className="font-medium">{results.competitive_landscape.competitive_position}</p>
              </div>
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">进入壁垒</p>
                <p className="font-medium">
                  {results.competitive_landscape.barriers_to_entry === "High" ? "高" :
                   results.competitive_landscape.barriers_to_entry === "Low" ? "低" : "中"}
                </p>
              </div>
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">威胁评估</p>
                <p className="text-sm">{results.competitive_landscape.threat_assessment}</p>
              </div>
            </div>

            {results.competitive_landscape.main_competitors && results.competitive_landscape.main_competitors.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">主要竞争对手</p>
                <div className="space-y-2">
                  {results.competitive_landscape.main_competitors.map((comp, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded bg-muted/50">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono">{comp.ticker}</Badge>
                        <span className="text-sm">{comp.name}</span>
                      </div>
                      <span className="text-xs text-muted-foreground">{comp.comparison}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Valuation Analysis */}
      {results.valuation_analysis && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <DollarSign className="h-5 w-5 text-accent" />
              </div>
              估值分析
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">公允价值</p>
                <p className="text-xl font-bold text-primary">{results.valuation_analysis.fair_value_estimate}</p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">vs 同行</p>
                <p className="font-medium">
                  {results.valuation_analysis.valuation_vs_peers === "Premium" ? "溢价" :
                   results.valuation_analysis.valuation_vs_peers === "Discount" ? "折价" : "持平"}
                </p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">vs 历史</p>
                <p className="font-medium">
                  {results.valuation_analysis.valuation_vs_history === "Above" ? "高于均值" :
                   results.valuation_analysis.valuation_vs_history === "Below" ? "低于均值" : "接近均值"}
                </p>
              </div>
              <div className="p-4 rounded-lg border border-border/40 text-center">
                <p className="text-xs text-muted-foreground mb-1">估值方法</p>
                <p className="text-sm">{results.valuation_analysis.methodology}</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-muted/50">
              <p className="text-xs text-muted-foreground mb-1">当前估值状况</p>
              <p className="text-sm">{results.valuation_analysis.current_valuation}</p>
            </div>

            {results.valuation_analysis.key_assumptions && results.valuation_analysis.key_assumptions.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">关键假设</p>
                <ul className="space-y-1">
                  {results.valuation_analysis.key_assumptions.map((assumption, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary">•</span>
                      {assumption}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Catalysts */}
      {results.catalysts && (
        <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-accent/10">
                <Zap className="h-5 w-5 text-accent" />
              </div>
              催化剂
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.catalysts.near_term && results.catalysts.near_term.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-3 flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    近期催化剂
                  </p>
                  <div className="space-y-2">
                    {results.catalysts.near_term.map((cat, i) => (
                      <div key={i} className="p-2 rounded bg-muted/50">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{cat.catalyst}</span>
                          <Badge variant="outline" className="text-xs">{cat.expected_timing}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{cat.potential_impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {results.catalysts.long_term && results.catalysts.long_term.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-3 flex items-center gap-1">
                    <Target className="h-4 w-4" />
                    长期催化剂
                  </p>
                  <div className="space-y-2">
                    {results.catalysts.long_term.map((cat, i) => (
                      <div key={i} className="p-2 rounded bg-muted/50">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{cat.catalyst}</span>
                          <Badge variant="outline" className="text-xs">{cat.expected_timing}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{cat.potential_impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Investment Recommendation */}
      {results.investment_recommendation && (
        <Card className="border-border/40 bg-gradient-to-r from-primary/5 to-accent/5 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="p-2 rounded-lg bg-primary/10">
                <Star className="h-5 w-5 text-primary" />
              </div>
              投资建议
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <p className="font-medium">{results.investment_recommendation.summary}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">适合投资者</p>
                <p className="text-sm">{results.investment_recommendation.ideal_investor_profile}</p>
              </div>
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">仓位配置</p>
                <Badge variant="secondary">
                  {results.investment_recommendation.position_sizing === "Core" ? "核心持仓" :
                   results.investment_recommendation.position_sizing === "Satellite" ? "卫星持仓" : "投机仓位"}
                </Badge>
              </div>
              <div className="p-3 rounded-lg border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">入场策略</p>
                <p className="text-sm">{results.investment_recommendation.entry_strategy}</p>
              </div>
            </div>

            {results.investment_recommendation.exit_triggers && results.investment_recommendation.exit_triggers.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">退出信号</p>
                <ul className="space-y-1">
                  {results.investment_recommendation.exit_triggers.map((trigger, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                      {trigger}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Data Sources & Disclaimers */}
      <Card className="border-border/40 bg-muted/30">
        <CardContent className="pt-6">
          <div className="space-y-4">
            {results.data_sources && (
              <div>
                <p className="text-xs font-medium mb-2 flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  数据来源
                </p>
                <div className="flex flex-wrap gap-2">
                  {results.data_sources.map((source, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {results.disclaimers && (
              <div className="pt-4 border-t">
                <p className="text-xs text-muted-foreground flex items-start gap-1">
                  <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  {results.disclaimers}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
