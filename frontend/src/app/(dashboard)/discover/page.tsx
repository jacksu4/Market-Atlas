"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Search, Rocket, Sparkles, Clock, Shield, FileText, Globe, Building2, ChevronDown, ChevronUp, Info } from "lucide-react";
import { cn } from "@/lib/utils";

// 投资时间范围选项
const timeHorizonOptions = [
  { value: "short", label: "短期", description: "1-3个月，关注催化剂和技术面", icon: "⚡" },
  { value: "medium", label: "中期", description: "6-12个月，关注基本面改善", icon: "📈" },
  { value: "long", label: "长期", description: "1年以上，关注长期增长趋势", icon: "🎯" },
];

// 风险偏好选项
const riskToleranceOptions = [
  { value: "conservative", label: "保守型", description: "偏好大盘蓝筹，低波动", color: "text-green-500" },
  { value: "moderate", label: "稳健型", description: "平衡风险与收益", color: "text-yellow-500" },
  { value: "aggressive", label: "激进型", description: "接受高波动，追求高回报", color: "text-red-500" },
];

// 报告深度选项
const reportDepthOptions = [
  { value: "quick", label: "快速摘要", description: "核心观点和推荐股票列表", time: "~2分钟" },
  { value: "standard", label: "标准报告", description: "包含评分、风险分析、投资逻辑", time: "~3分钟" },
  { value: "comprehensive", label: "深度分析", description: "详细财务分析、竞争格局、估值模型", time: "~5分钟" },
];

// 市场地区选项
const marketRegionOptions = [
  { value: "us", label: "美股", flag: "🇺🇸" },
  { value: "us_adr", label: "美股+ADR", flag: "🌐" },
];

// 行业偏好选项
const sectorOptions = [
  { value: "technology", label: "科技" },
  { value: "healthcare", label: "医疗健康" },
  { value: "financials", label: "金融" },
  { value: "consumer", label: "消费" },
  { value: "industrials", label: "工业" },
  { value: "energy", label: "能源" },
  { value: "materials", label: "材料" },
  { value: "utilities", label: "公用事业" },
  { value: "real_estate", label: "房地产" },
  { value: "communication", label: "通信" },
];

export default function DiscoverPage() {
  const router = useRouter();
  const [theme, setTheme] = useState("");
  const [title, setTitle] = useState("");
  const [additionalCriteria, setAdditionalCriteria] = useState("");
  const [loading, setLoading] = useState(false);

  // 新增的选项状态
  const [timeHorizon, setTimeHorizon] = useState("medium");
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [reportDepth, setReportDepth] = useState("standard");
  const [marketRegion, setMarketRegion] = useState("us");
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  const handleStartDiscovery = async () => {
    if (!theme.trim()) {
      toast.error("请输入研究主题");
      return;
    }

    setLoading(true);
    try {
      // 构建增强的criteria
      const enhancedCriteria = buildEnhancedCriteria();

      const task = await api.createDiscoveryTask({
        title: title.trim() || `Discovery: ${theme}`,
        theme: theme.trim(),
        additional_criteria: enhancedCriteria,
      });

      toast.success("研究任务已启动");
      router.push(`/research/${task.id}`);
    } catch (error) {
      toast.error("启动研究失败");
    } finally {
      setLoading(false);
    }
  };

  const buildEnhancedCriteria = () => {
    const parts: string[] = [];

    // 时间范围
    const timeDesc = timeHorizonOptions.find(t => t.value === timeHorizon);
    if (timeDesc) {
      parts.push(`投资时间范围: ${timeDesc.label} (${timeDesc.description})`);
    }

    // 风险偏好
    const riskDesc = riskToleranceOptions.find(r => r.value === riskTolerance);
    if (riskDesc) {
      parts.push(`风险偏好: ${riskDesc.label} (${riskDesc.description})`);
    }

    // 报告深度
    const depthDesc = reportDepthOptions.find(d => d.value === reportDepth);
    if (depthDesc) {
      parts.push(`报告深度: ${depthDesc.label}`);
    }

    // 市场地区
    const regionDesc = marketRegionOptions.find(m => m.value === marketRegion);
    if (regionDesc) {
      parts.push(`市场: ${regionDesc.label}`);
    }

    // 行业偏好
    if (selectedSectors.length > 0) {
      const sectorLabels = selectedSectors.map(s =>
        sectorOptions.find(opt => opt.value === s)?.label || s
      );
      parts.push(`行业偏好: ${sectorLabels.join(", ")}`);
    }

    // 用户自定义criteria
    if (additionalCriteria.trim()) {
      parts.push(`其他要求: ${additionalCriteria.trim()}`);
    }

    return parts.join("\n");
  };

  const toggleSector = (sector: string) => {
    setSelectedSectors(prev =>
      prev.includes(sector)
        ? prev.filter(s => s !== sector)
        : [...prev, sector]
    );
  };

  const quickThemes = [
    { label: "AI 基础设施", theme: "AI infrastructure and GPU computing companies" },
    { label: "边缘计算", theme: "Edge computing and IoT platforms" },
    { label: "网络安全", theme: "Next-generation cybersecurity" },
    { label: "机器人", theme: "Robotics and automation" },
    { label: "云原生", theme: "Cloud-native infrastructure" },
    { label: "量子计算", theme: "Quantum computing" },
    { label: "清洁能源", theme: "Clean energy and renewable technology" },
    { label: "生物科技", theme: "Biotechnology and gene therapy" },
  ];

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-4xl font-bold tracking-tight gradient-text">Discover</h1>
        <p className="text-muted-foreground mt-2">
          使用AI发现潜在的投资机会
        </p>
      </div>

      <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <div className="p-2 rounded-lg bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            AI Discovery
          </CardTitle>
          <CardDescription className="text-base">
            描述一个投资主题，AI将为您进行深度研究并识别潜在标的
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 任务标题 */}
          <div className="space-y-2">
            <Label htmlFor="title">任务标题 (可选)</Label>
            <Input
              id="title"
              placeholder="例如：2026年Q1 AI基础设施研究"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* 研究主题 */}
          <div className="space-y-2">
            <Label htmlFor="theme">研究主题 *</Label>
            <Textarea
              id="theme"
              placeholder="例如：专注于AI基础设施的公司，包括GPU/TPU制造商、数据中心运营商、以及专注于AI工作负载的云计算服务提供商"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              rows={3}
            />
          </div>

          {/* 快速主题标签 */}
          <div>
            <Label className="text-sm text-muted-foreground mb-3 block">
              热门主题:
            </Label>
            <div className="flex flex-wrap gap-2">
              {quickThemes.map((qt) => (
                <Button
                  key={qt.label}
                  variant="outline"
                  size="sm"
                  onClick={() => setTheme(qt.theme)}
                  className={cn(
                    "border-border/40 hover:border-primary/50 hover:bg-primary/5 transition-all duration-200",
                    theme === qt.theme && "border-primary bg-primary/10"
                  )}
                >
                  {qt.label}
                </Button>
              ))}
            </div>
          </div>

          {/* 投资时间范围 */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              投资时间范围
            </Label>
            <div className="grid grid-cols-3 gap-3">
              {timeHorizonOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTimeHorizon(option.value)}
                  className={cn(
                    "p-3 rounded-lg border text-left transition-all duration-200",
                    timeHorizon === option.value
                      ? "border-primary bg-primary/10"
                      : "border-border/40 hover:border-primary/50 hover:bg-muted/50"
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span>{option.icon}</span>
                    <span className="font-medium">{option.label}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* 风险偏好 */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              风险偏好
            </Label>
            <div className="grid grid-cols-3 gap-3">
              {riskToleranceOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setRiskTolerance(option.value)}
                  className={cn(
                    "p-3 rounded-lg border text-left transition-all duration-200",
                    riskTolerance === option.value
                      ? "border-primary bg-primary/10"
                      : "border-border/40 hover:border-primary/50 hover:bg-muted/50"
                  )}
                >
                  <div className={cn("font-medium mb-1", option.color)}>{option.label}</div>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* 报告深度 */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              报告深度
            </Label>
            <div className="grid grid-cols-3 gap-3">
              {reportDepthOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setReportDepth(option.value)}
                  className={cn(
                    "p-3 rounded-lg border text-left transition-all duration-200",
                    reportDepth === option.value
                      ? "border-primary bg-primary/10"
                      : "border-border/40 hover:border-primary/50 hover:bg-muted/50"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{option.label}</span>
                    <span className="text-xs text-muted-foreground">{option.time}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* 高级选项折叠 */}
          <div className="border-t pt-4">
            <button
              onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {showAdvancedOptions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              高级选项
            </button>

            {showAdvancedOptions && (
              <div className="mt-4 space-y-4">
                {/* 市场地区 */}
                <div className="space-y-3">
                  <Label className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    市场地区
                  </Label>
                  <div className="flex gap-3">
                    {marketRegionOptions.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setMarketRegion(option.value)}
                        className={cn(
                          "px-4 py-2 rounded-lg border transition-all duration-200",
                          marketRegion === option.value
                            ? "border-primary bg-primary/10"
                            : "border-border/40 hover:border-primary/50 hover:bg-muted/50"
                        )}
                      >
                        <span className="mr-2">{option.flag}</span>
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 行业偏好 */}
                <div className="space-y-3">
                  <Label className="flex items-center gap-2">
                    <Building2 className="h-4 w-4" />
                    行业偏好 (可多选，留空则不限制)
                  </Label>
                  <div className="flex flex-wrap gap-2">
                    {sectorOptions.map((sector) => (
                      <button
                        key={sector.value}
                        onClick={() => toggleSector(sector.value)}
                        className={cn(
                          "px-3 py-1.5 rounded-full border text-sm transition-all duration-200",
                          selectedSectors.includes(sector.value)
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border/40 hover:border-primary/50 hover:bg-muted/50"
                        )}
                      >
                        {sector.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 额外条件 */}
                <div className="space-y-2">
                  <Label htmlFor="criteria">其他筛选条件 (可选)</Label>
                  <Textarea
                    id="criteria"
                    placeholder="例如：市值大于100亿美元、美股上市、收入正增长、近期有重大产品发布"
                    value={additionalCriteria}
                    onChange={(e) => setAdditionalCriteria(e.target.value)}
                    rows={2}
                  />
                </div>
              </div>
            )}
          </div>

          {/* 提示信息 */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/50 border border-border/40">
            <Info className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
            <p className="text-xs text-muted-foreground">
              AI将根据您的选择生成专业的研究报告，包含：股票推荐、评分标准、投资逻辑、风险分析、财务指标等。报告深度越高，分析越详细。
            </p>
          </div>

          {/* 启动按钮 */}
          <Button
            onClick={handleStartDiscovery}
            disabled={loading || !theme.trim()}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all duration-200"
            size="lg"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin mr-2"></div>
                正在启动研究...
              </>
            ) : (
              <>
                <Rocket className="h-5 w-5 mr-2" />
                开始 AI Discovery
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Deep Dive 部分 */}
      <Card className="border-border/40 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <div className="p-2 rounded-lg bg-accent/10">
              <Search className="h-5 w-5 text-accent" />
            </div>
            Deep Dive Research
          </CardTitle>
          <CardDescription className="text-base">
            对特定股票进行深度研究分析
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DeepDiveForm />
        </CardContent>
      </Card>
    </div>
  );
}

function DeepDiveForm() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);

  const handleStartDeepDive = async () => {
    if (!ticker.trim()) {
      toast.error("请输入股票代码");
      return;
    }

    setLoading(true);
    try {
      const task = await api.createDeepDiveTask({
        title: `Deep Dive: ${ticker.toUpperCase()}`,
        ticker: ticker.trim().toUpperCase(),
      });

      toast.success("深度研究已启动");
      router.push(`/research/${task.id}`);
    } catch (error) {
      toast.error("启动研究失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-4">
      <Input
        placeholder="输入股票代码 (例如 NVDA)"
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
        className="max-w-[200px]"
        onKeyDown={(e) => e.key === "Enter" && handleStartDeepDive()}
      />
      <Button onClick={handleStartDeepDive} disabled={loading || !ticker.trim()}>
        {loading ? "启动中..." : "开始研究"}
      </Button>
    </div>
  );
}
