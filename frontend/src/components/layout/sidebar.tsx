"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  ListChecks,
  Search,
  FileText,
  Settings,
  LogOut,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Watchlist", href: "/watchlist", icon: ListChecks },
  { name: "Discover", href: "/discover", icon: Search },
  { name: "Research", href: "/research", icon: FileText },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
  };

  return (
    <div className="flex h-full w-64 flex-col border-r border-border/40 bg-sidebar/50 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex h-20 items-center border-b border-border/40 px-6">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 blur-md rounded-lg group-hover:bg-primary/30 transition-all"></div>
            <div className="relative bg-primary/10 p-2 rounded-lg border border-primary/30 group-hover:border-primary/50 transition-all">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold tracking-tight gradient-text">Market Atlas</span>
            <span className="text-xs text-muted-foreground">Investment Research</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-6">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary/10 text-primary shadow-lg shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              )}
            >
              {/* Active indicator */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full glow-sm" />
              )}

              <div className={cn(
                "p-1.5 rounded-lg transition-all",
                isActive
                  ? "bg-primary/20"
                  : "group-hover:bg-primary/10"
              )}>
                <item.icon className="h-4 w-4" />
              </div>

              <span className="relative">
                {item.name}
                {isActive && (
                  <div className="absolute -bottom-0.5 left-0 right-0 h-px bg-gradient-to-r from-primary/0 via-primary/50 to-primary/0" />
                )}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border/40 p-3">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl transition-all"
          onClick={handleLogout}
        >
          <div className="p-1.5 rounded-lg group-hover:bg-destructive/10 transition-all">
            <LogOut className="h-4 w-4" />
          </div>
          Sign Out
        </Button>

        {/* Version badge */}
        <div className="mt-3 px-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground/60">
            <span>v1.0.0</span>
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
              <span>Live</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
