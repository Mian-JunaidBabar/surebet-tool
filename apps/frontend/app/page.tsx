import {
  ArrowRight,
  Shield,
  TrendingUp,
  Zap,
  Search,
  Calculator,
  ShieldCheck,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <div className="relative">
      {/* Hero with vibrant gradient */}
      <div className="absolute inset-0 -z-10 bg-linear-to-br from-primary/20 via-secondary/10 to-accent/20" />
      <section className="container mx-auto px-4 pt-20 pb-12">
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
              Find Profitable Surebets
              <span className="text-primary"> Instantly</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Discover arbitrage opportunities across multiple bookmakers in
              real-time. Unlock consistent, risk-managed profits.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4">
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

          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 w-full max-w-5xl">
            {[
              {
                icon: <Zap className="h-10 w-10 text-primary" />,
                title: "Real-Time Detection",
                desc: "Instantly spot arbitrage opportunities across markets.",
              },
              {
                icon: <TrendingUp className="h-10 w-10 text-primary" />,
                title: "Maximize Profits",
                desc: "Auto-calculated stakes for optimal returns.",
              },
              {
                icon: <Shield className="h-10 w-10 text-primary" />,
                title: "Risk-Managed",
                desc: "Structured approach to minimize exposure.",
              },
            ].map((f, i) => (
              <Card key={i} className="border bg-card/60 backdrop-blur">
                <CardContent className="flex flex-col items-center space-y-2 p-6">
                  {f.icon}
                  <h3 className="font-semibold text-lg">{f.title}</h3>
                  <p className="text-sm text-muted-foreground text-center">
                    {f.desc}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="container mx-auto px-4 py-16">
        <div className="mx-auto max-w-3xl text-center mb-10">
          <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
          <p className="text-muted-foreground mt-2">
            Three simple steps to start generating consistent returns from
            market inefficiencies.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border bg-card/60 backdrop-blur">
            <CardContent className="p-6 space-y-3 text-center">
              <Search className="h-8 w-8 text-primary mx-auto" />
              <h3 className="font-semibold text-lg">1. Scan Odds</h3>
              <p className="text-sm text-muted-foreground">
                We continuously scan bookmakers to surface cross-market
                discrepancies.
              </p>
            </CardContent>
          </Card>
          <Card className="border bg-card/60 backdrop-blur">
            <CardContent className="p-6 space-y-3 text-center">
              <Calculator className="h-8 w-8 text-primary mx-auto" />
              <h3 className="font-semibold text-lg">2. Compute Stakes</h3>
              <p className="text-sm text-muted-foreground">
                Automatic stake calculation distributes capital for guaranteed
                outcomes.
              </p>
            </CardContent>
          </Card>
          <Card className="border bg-card/60 backdrop-blur">
            <CardContent className="p-6 space-y-3 text-center">
              <ShieldCheck className="h-8 w-8 text-primary mx-auto" />
              <h3 className="font-semibold text-lg">3. Place Bets</h3>
              <p className="text-sm text-muted-foreground">
                Execute with your preferred books and lock in the arbitrage
                spread.
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="mt-10 flex justify-center">
          <Link href="/dashboard">
            <Button size="lg">Start Finding Surebets</Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
