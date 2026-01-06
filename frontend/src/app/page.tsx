import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-background to-muted">
      <div className="max-w-3xl mx-auto text-center px-4">
        <h1 className="text-5xl font-bold tracking-tight mb-6">
          Market Atlas
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          AI-powered investment research platform for fund managers.
          Track your watchlist, analyze SEC filings, and discover new opportunities.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/login">
            <Button size="lg">
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button size="lg" variant="outline">
              Create Account
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
