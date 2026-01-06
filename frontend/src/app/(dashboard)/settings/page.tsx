"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { User } from "@/types";
import { toast } from "sonner";
import { MessageCircle, Bell, Shield, ExternalLink, Loader2 } from "lucide-react";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [savingPreferences, setSavingPreferences] = useState<string | null>(null);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const data = await api.getCurrentUser();
      setUser(data);
    } catch (error) {
      toast.error("Failed to load user settings");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateTelegramLink = async () => {
    try {
      const { link } = await api.generateTelegramLink();
      setTelegramLink(link);
      toast.success("Telegram connection link generated! Click to open.");
    } catch (error) {
      toast.error("Failed to generate link");
    }
  };

  const handleDisconnectTelegram = async () => {
    try {
      const updatedUser = await api.disconnectTelegram();
      setUser(updatedUser);
      toast.success("Telegram disconnected");
    } catch (error) {
      toast.error("Failed to disconnect");
    }
  };

  const handleTogglePreference = async (key: string, value: boolean) => {
    setSavingPreferences(key);
    try {
      const updatedUser = await api.updateNotificationPreferences({
        [key]: value,
      });
      setUser(updatedUser);
      toast.success("Preference saved");
    } catch (error) {
      toast.error("Failed to save");
    } finally {
      setSavingPreferences(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  const prefs = user?.settings?.notification_preferences || {
    news_alerts: true,
    filing_alerts: true,
    research_complete: true,
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Profile Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Profile
          </CardTitle>
          <CardDescription>Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Name</Label>
              <Input value={user?.name || ""} disabled />
            </div>
            <div>
              <Label>Email</Label>
              <Input value={user?.email || ""} disabled />
            </div>
          </div>
          <div>
            <Label>Member Since</Label>
            <Input
              value={
                user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : ""
              }
              disabled
            />
          </div>
        </CardContent>
      </Card>

      {/* Telegram Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Telegram Notifications
          </CardTitle>
          <CardDescription>
            Connect your Telegram account to receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {user?.settings?.telegram_chat_id ? (
            <div className="rounded-lg border p-4 bg-green-50 dark:bg-green-900/20">
              <p className="font-medium text-green-900 dark:text-green-100">
                ✓ Connected
              </p>
              <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                You'll receive notifications on Telegram
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDisconnectTelegram}
                className="mt-3"
              >
                Disconnect
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg border p-4 bg-muted/50">
                <h4 className="font-medium mb-2">How to connect:</h4>
                <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-1">
                  <li>Click "Generate Connection Link" below</li>
                  <li>Open the link in Telegram</li>
                  <li>Send /start to the bot</li>
                  <li>You'll receive a confirmation message</li>
                </ol>
              </div>

              {telegramLink ? (
                <div className="space-y-2">
                  <a
                    href={telegramLink}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button className="w-full">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Telegram to Connect
                    </Button>
                  </a>
                  <p className="text-xs text-muted-foreground text-center">
                    Link expires in 10 minutes
                  </p>
                </div>
              ) : (
                <Button onClick={handleGenerateTelegramLink} className="w-full">
                  Generate Connection Link
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notification Preferences
          </CardTitle>
          <CardDescription>
            Choose what notifications you want to receive
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-medium">Important News Alerts</p>
              <p className="text-sm text-muted-foreground">
                Get notified about high-importance news for your watchlist stocks
              </p>
            </div>
            <Switch
              checked={prefs.news_alerts}
              disabled={savingPreferences === "news_alerts"}
              onCheckedChange={(checked) =>
                handleTogglePreference("news_alerts", checked)
              }
            />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-medium">SEC Filing Alerts</p>
              <p className="text-sm text-muted-foreground">
                Get notified when new SEC filings are analyzed
              </p>
            </div>
            <Switch
              checked={prefs.filing_alerts}
              disabled={savingPreferences === "filing_alerts"}
              onCheckedChange={(checked) =>
                handleTogglePreference("filing_alerts", checked)
              }
            />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-medium">Research Complete</p>
              <p className="text-sm text-muted-foreground">
                Get notified when a research task completes
              </p>
            </div>
            <Switch
              checked={prefs.research_complete}
              disabled={savingPreferences === "research_complete"}
              onCheckedChange={(checked) =>
                handleTogglePreference("research_complete", checked)
              }
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
