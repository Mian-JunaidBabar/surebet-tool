"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import React, { useState, useEffect } from "react";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
  SheetClose,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useParams } from "next/navigation";

type Outcome = {
  id: number;
  event_id: number;
  bookmaker: string;
  name: string;
  odds: number;
  deep_link_url: string;
};

type SurebetEvent = {
  id: number;
  event_id: string;
  event: string;
  sport: string;
  outcomes: Outcome[];
  profit_percentage: number;
  total_inverse_odds: number;
};

async function fetchSurebet(eventId: string): Promise<SurebetEvent | null> {
  try {
    const BACKEND =
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      process.env.BACKEND_URL ||
      "http://backend:8000";

    const res = await fetch(
      `${BACKEND}/api/v1/surebets/${encodeURIComponent(eventId)}`,
      {
        next: { revalidate: 10 },
        cache: "no-store",
      }
    );
    if (!res.ok) return null;
    const item = (await res.json()) as SurebetEvent;
    return item || null;
  } catch {
    return null;
  }
}

type PlainEvent = {
  id: number;
  event_id: string;
  event: string;
  sport: string;
  outcomes: Outcome[];
};

async function fetchEvent(eventId: string): Promise<PlainEvent | null> {
  try {
    const BACKEND =
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      process.env.BACKEND_URL ||
      "http://backend:8000";

    const res = await fetch(
      `${BACKEND}/api/v1/events/${encodeURIComponent(eventId)}`,
      {
        next: { revalidate: 10 },
        cache: "no-store",
      }
    );
    if (!res.ok) return null;
    const item = (await res.json()) as PlainEvent;
    return item || null;
  } catch {
    return null;
  }
}

export default function BetDetailPage() {
  const params = useParams();
  const eventId = params.eventId as string;

  const [surebet, setSurebet] = useState<SurebetEvent | null>(null);
  const [plain, setPlain] = useState<PlainEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    async function fetchData() {
      if (!eventId) return;

      setLoading(true);
      setError(null);

      try {
        // Try surebet first
        const surebetData = await fetchSurebet(eventId);
        if (surebetData) {
          setSurebet(surebetData);
          setLoading(false);
          return;
        }

        // Fallback to plain event
        const plainData = await fetchEvent(eventId);
        if (plainData) {
          setPlain(plainData);
          setLoading(false);
          return;
        }

        // Neither found
        setError("Event not found");
      } catch (err) {
        setError("Failed to load event data");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [eventId]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (error || (!surebet && !plain)) {
    notFound();
  }

  const event = (surebet || plain)!;

  // Build best outcomes by outcome name
  const bestByName = event.outcomes.reduce<Record<string, Outcome>>(
    (acc, curr) => {
      const key = curr.name || "";
      if (!key) return acc;
      if (!acc[key] || curr.odds > acc[key].odds) acc[key] = curr;
      return acc;
    },
    {}
  );
  const bestOutcomes = Object.values(bestByName);
  const bestLinks = bestOutcomes
    .map((o) => o.deep_link_url)
    .filter(Boolean)
    .slice(0, 3);

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6 flex items-center justify-between gap-2">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Bet Details</h1>
          <p className="text-muted-foreground text-sm">
            Event breakdown and top odds
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
            <SheetTrigger asChild>
              <Button variant="outline">Calculate Stakes</Button>
            </SheetTrigger>
            <SheetContent side="right">
              <SheetHeader>
                <SheetTitle>Calculate Stakes</SheetTitle>
                <SheetDescription>
                  Allocate a stake amount across the best odds to ensure a
                  consistent return.
                </SheetDescription>
              </SheetHeader>

              <div className="p-4">
                <CalculateStakesForm outcomes={bestOutcomes} />
              </div>

              <SheetFooter>
                <SheetClose asChild>
                  <Button variant="outline">Close</Button>
                </SheetClose>
              </SheetFooter>
            </SheetContent>
          </Sheet>
          <Link href="/dashboard">
            <Button variant="outline">Back to Dashboard</Button>
          </Link>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-3">
            <span className="truncate max-w-[70vw]" title={event.event}>
              {event.event}
            </span>
            <Badge variant="secondary">{event.sport}</Badge>
            {surebet ? (
              <Badge variant="default" className="ml-auto">
                Profit: {surebet.profit_percentage.toFixed(2)}%
              </Badge>
            ) : (
              <Badge variant="outline" className="ml-auto">
                Not currently a surebet
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <div>Event ID: {event.event_id}</div>
          {surebet && (
            <div>
              Arbitrage (inverse odds): {surebet.total_inverse_odds.toFixed(4)}
            </div>
          )}
          {bestLinks.length > 0 && (
            <div className="pt-2">
              <Button
                onClick={() =>
                  bestLinks.forEach((href) =>
                    window.open(href, "_blank", "noopener,noreferrer")
                  )
                }
                className="gap-2"
              >
                <ExternalLink className="h-4 w-4" /> Open Best Bookmakers
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Available Odds</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {event.outcomes.map((out) => {
              const isBest = bestByName[out.name]?.id === out.id;
              return (
                <div
                  key={out.id}
                  className={`border rounded-md p-3 text-sm flex items-center justify-between ${
                    isBest ? "bg-green-50 dark:bg-green-950/30" : ""
                  }`}
                >
                  <div className="min-w-0 pr-3">
                    <div className="font-medium truncate" title={out.bookmaker}>
                      {out.bookmaker}
                    </div>
                    <div className="text-muted-foreground truncate">
                      {out.name}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="font-semibold">{out.odds.toFixed(2)}</div>
                    {out.deep_link_url ? (
                      <Link
                        href={out.deep_link_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex"
                      >
                        <Button size="sm" variant="ghost" className="gap-1">
                          <ExternalLink className="h-4 w-4" />
                          Bet
                        </Button>
                      </Link>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CalculateStakesForm({ outcomes }: { outcomes: Outcome[] }) {
  const [stake, setStake] = useState<number>(100);

  const sumInverse = outcomes.reduce((acc, o) => acc + 1 / o.odds, 0);
  if (!outcomes || outcomes.length === 0) {
    return <div className="text-sm">No outcomes available</div>;
  }
  if (sumInverse <= 0) {
    return (
      <div className="text-sm text-amber-600">
        Unable to calculate stakes: invalid odds or division by zero
      </div>
    );
  }

  const results = outcomes.map((o) => {
    const share = 1 / o.odds / sumInverse;
    const stakeForOutcome = stake * share;
    const potentialReturn = stakeForOutcome * o.odds;
    return {
      ...o,
      stake: stakeForOutcome,
      return: potentialReturn,
    };
  });

  const guaranteedReturn = stake / sumInverse;
  const profit = guaranteedReturn - stake;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-2">
        <Label>Stake Amount (Total)</Label>
        <Input
          type="number"
          min={1}
          value={stake}
          onChange={(e) => setStake(Number(e.target.value))}
        />
      </div>

      <div className="text-sm">
        <div>
          Expected return: <b>{guaranteedReturn?.toFixed(2)}</b>
        </div>
        <div>
          Profit: <b>{profit?.toFixed(2)}</b>
        </div>
      </div>

      <div className="space-y-2">
        {results.map((r) => (
          <div
            key={r.id}
            className={cn(
              "p-2 border rounded flex justify-between items-center",
              "text-sm"
            )}
          >
            <div>
              <div className="font-medium">{r.bookmaker}</div>
              <div className="text-muted-foreground">
                {r.name} @ {r.odds.toFixed(2)}
              </div>
            </div>
            <div className="text-right">
              <div className="font-semibold">{r.stake.toFixed(2)}</div>
              <div className="text-muted-foreground">
                Return {r.return.toFixed(2)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
