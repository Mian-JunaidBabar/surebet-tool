import { ArrowRight, Shield, TrendingUp, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="flex flex-col items-center justify-center min-h-[80vh] text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
            Find Profitable Surebets
            <span className="text-primary"> Instantly</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Discover arbitrage betting opportunities across multiple bookmakers
            in real-time. Guaranteed profit on every bet.
          </p>
        </div>

        <div className="flex-4 gap-4">
          <Link href="/dashboard" className="gap-2">
            <Button size="lg">
              View Live Surebets
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>

          <Link href="/settings" className="gap-2">
            <Button size="lg" variant="outline">
              Configure Settings
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8 w-full max-w-4xl">
          <div className="flex flex-col items-center space-y-2 p-6 rounded-lg border bg-card">
            <Zap className="h-10 w-10 text-primary" />
            <h3 className="font-semibold text-lg">Real-Time Detection</h3>
            <p className="text-sm text-muted-foreground text-center">
              Get instant notifications when new surebets are found
            </p>
          </div>
          <div className="flex flex-col items-center space-y-2 p-6 rounded-lg border bg-card">
            <TrendingUp className="h-10 w-10 text-primary" />
            <h3 className="font-semibold text-lg">Maximize Profits</h3>
            <p className="text-sm text-muted-foreground text-center">
              Calculate optimal stake distribution automatically
            </p>
          </div>
          <div className="flex flex-col items-center space-y-2 p-6 rounded-lg border bg-card">
            <Shield className="h-10 w-10 text-primary" />
            <h3 className="font-semibold text-lg">Risk-Free Betting</h3>
            <p className="text-sm text-muted-foreground text-center">
              Guaranteed profit regardless of the outcome
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
