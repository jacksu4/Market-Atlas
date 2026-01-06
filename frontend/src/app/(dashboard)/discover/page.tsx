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
import { Search, Rocket, Sparkles } from "lucide-react";

export default function DiscoverPage() {
  const router = useRouter();
  const [theme, setTheme] = useState("");
  const [title, setTitle] = useState("");
  const [additionalCriteria, setAdditionalCriteria] = useState("");
  const [loading, setLoading] = useState(false);

  const handleStartDiscovery = async () => {
    if (!theme.trim()) {
      toast.error("Please enter a research theme");
      return;
    }

    setLoading(true);
    try {
      const task = await api.createDiscoveryTask({
        title: title.trim() || `Discovery: ${theme}`,
        theme: theme.trim(),
        additional_criteria: additionalCriteria.trim() || undefined,
      });

      toast.success("Discovery task started");
      router.push(`/research/${task.id}`);
    } catch (error) {
      toast.error("Failed to start discovery");
    } finally {
      setLoading(false);
    }
  };

  const quickThemes = [
    { label: "AI Infrastructure", theme: "AI infrastructure and GPU computing" },
    { label: "Edge Computing", theme: "Edge computing and IoT platforms" },
    { label: "Cybersecurity", theme: "Next-generation cybersecurity" },
    { label: "Robotics", theme: "Robotics and automation" },
    { label: "Cloud Native", theme: "Cloud-native infrastructure" },
    { label: "Quantum Computing", theme: "Quantum computing" },
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold">Discover</h1>
        <p className="text-muted-foreground">
          Use AI to find potential investment opportunities
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            AI Discovery
          </CardTitle>
          <CardDescription>
            Describe an investment theme and our AI will research and identify potential stocks
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title">Task Title (optional)</Label>
            <Input
              id="title"
              placeholder="e.g., Q1 2025 AI Infrastructure Research"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="theme">Research Theme</Label>
            <Textarea
              id="theme"
              placeholder="e.g., Companies building AI infrastructure, including GPU/TPU manufacturers, data center operators, and cloud computing providers focused on AI workloads"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              rows={3}
            />
          </div>

          <div>
            <Label className="text-sm text-muted-foreground mb-2 block">
              Quick themes:
            </Label>
            <div className="flex flex-wrap gap-2">
              {quickThemes.map((qt) => (
                <Button
                  key={qt.label}
                  variant="outline"
                  size="sm"
                  onClick={() => setTheme(qt.theme)}
                >
                  {qt.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="criteria">Additional Criteria (optional)</Label>
            <Textarea
              id="criteria"
              placeholder="e.g., Market cap above $1B, US-listed, positive revenue growth"
              value={additionalCriteria}
              onChange={(e) => setAdditionalCriteria(e.target.value)}
              rows={2}
            />
          </div>

          <Button
            onClick={handleStartDiscovery}
            disabled={loading || !theme.trim()}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>Launching Discovery...</>
            ) : (
              <>
                <Rocket className="h-4 w-4 mr-2" />
                Start Discovery
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Deep Dive Research
          </CardTitle>
          <CardDescription>
            Run comprehensive research on a specific stock
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
      toast.error("Please enter a ticker symbol");
      return;
    }

    setLoading(true);
    try {
      const task = await api.createDeepDiveTask({
        title: `Deep Dive: ${ticker.toUpperCase()}`,
        ticker: ticker.trim().toUpperCase(),
      });

      toast.success("Deep dive started");
      router.push(`/research/${task.id}`);
    } catch (error) {
      toast.error("Failed to start deep dive");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-4">
      <Input
        placeholder="Enter ticker (e.g., NVDA)"
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
        className="max-w-[200px]"
      />
      <Button onClick={handleStartDeepDive} disabled={loading || !ticker.trim()}>
        {loading ? "Starting..." : "Research"}
      </Button>
    </div>
  );
}
