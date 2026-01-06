"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { User } from "@/types";
import { toast } from "sonner";
import { MessageCircle, Bell, Shield } from "lucide-react";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [telegramChatId, setTelegramChatId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getCurrentUser()
      .then((data) => {
        setUser(data);
        setTelegramChatId(data.settings?.telegram_chat_id || "");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSaveTelegram = () => {
    toast.success("Telegram settings saved");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and preferences
        </p>
      </div>

      {/* Profile */}
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
            <div className="space-y-2">
              <Label>Name</Label>
              <Input value={user?.name || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user?.email || ""} disabled />
            </div>
          </div>
          <div className="space-y-2">
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

      {/* Telegram */}
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
          <div className="rounded-lg border p-4 bg-muted/50">
            <h4 className="font-medium mb-2">How to connect:</h4>
            <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-1">
              <li>Open Telegram and search for <code className="bg-muted px-1 rounded">@market_atlas_bot</code></li>
              <li>Start a conversation with the bot</li>
              <li>The bot will give you a Chat ID</li>
              <li>Enter the Chat ID below</li>
            </ol>
          </div>

          <div className="space-y-2">
            <Label htmlFor="telegram">Telegram Chat ID</Label>
            <div className="flex gap-2">
              <Input
                id="telegram"
                placeholder="Enter your Chat ID"
                value={telegramChatId}
                onChange={(e) => setTelegramChatId(e.target.value)}
              />
              <Button onClick={handleSaveTelegram}>Save</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
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
            <div>
              <p className="font-medium">Important News Alerts</p>
              <p className="text-sm text-muted-foreground">
                Get notified about significant news for your watchlist stocks
              </p>
            </div>
            <Button variant="outline" size="sm">
              Enabled
            </Button>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">SEC Filing Alerts</p>
              <p className="text-sm text-muted-foreground">
                Get notified when new SEC filings are detected
              </p>
            </div>
            <Button variant="outline" size="sm">
              Enabled
            </Button>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Research Complete</p>
              <p className="text-sm text-muted-foreground">
                Get notified when a research task completes
              </p>
            </div>
            <Button variant="outline" size="sm">
              Enabled
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
