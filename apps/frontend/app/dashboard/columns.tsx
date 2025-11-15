"use client";

import { ColumnDef } from "@tanstack/react-table";
import { ExternalLink, MoreHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Link from "next/link";
import React, { useState } from "react";
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

// Updated TypeScript types matching backend SurebetEvent schema
export type SurebetEvent = {
  id: number;
  event_id: string;
  event: string;
  sport: string;
  outcomes: Array<{
    id: number;
    event_id: number;
    bookmaker: string;
    name: string;
    odds: number;
    deep_link_url: string;
  }>;
  profit_percentage: number;
  total_inverse_odds: number;
};

export const columns: ColumnDef<SurebetEvent>[] = [
  {
    accessorKey: "profit_percentage",
    header: "Profit",
    cell: ({ row }: { row: any }) => {
      const profit = row.getValue("profit_percentage") as number;
      return (
        <Badge variant="default" className="font-semibold">
          {profit.toFixed(2)}%
        </Badge>
      );
    },
    filterFn: (row, id, value) => {
      const profit = row.getValue(id) as number;
      const [min, max] = value as [number, number];
      return profit >= min && profit <= max;
    },
  },
  {
    accessorKey: "event",
    header: "Event",
    cell: ({ row }: { row: any }) => {
      const event = row.getValue("event") as string;
      const sport = row.original.sport;

      // Aggressively truncate event names to prevent table overflow
      const maxLength = 45;
      const displayEvent =
        event.length > maxLength
          ? event.substring(0, maxLength) + "..."
          : event;

      return (
        <div className="flex flex-col max-w-[200px]">
          <span className="font-medium truncate" title={event}>
            {displayEvent}
          </span>
          <span className="text-xs text-muted-foreground truncate">
            {sport}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: "sport",
    header: "Sport",
    cell: ({ row }: { row: any }) => {
      const sport = row.getValue("sport") as string;
      return <span className="text-sm">{sport}</span>;
    },
  },
  {
    accessorKey: "outcomes",
    header: "Bets",
    cell: ({ row }: { row: any }) => {
      const outcomes = row.getValue("outcomes") as SurebetEvent["outcomes"];

      // Group outcomes by name (e.g., "Home Win", "Draw", "Away Win")
      // and pick the best odds for each outcome type
      const bestByOutcomeName = outcomes.reduce(
        (acc: Record<string, (typeof outcomes)[number]>, curr) => {
          const key = curr.name || "";
          if (!key) return acc;
          if (!acc[key] || curr.odds > acc[key].odds) {
            acc[key] = curr;
          }
          return acc;
        },
        {}
      );

      const bestOutcomes = Object.values(bestByOutcomeName);
      const maxDisplay = 3; // Show max 3 outcomes (typical for 3-way markets)
      const displayOutcomes = bestOutcomes.slice(0, maxDisplay);
      const remainingCount = bestOutcomes.length - displayOutcomes.length;

      return (
        <div className="flex flex-col gap-1 max-w-[280px]">
          {displayOutcomes.map(
            (outcome: SurebetEvent["outcomes"][0], index: number) => {
              // Truncate bookmaker name if too long
              const bookmaker =
                outcome.bookmaker.length > 18
                  ? outcome.bookmaker.substring(0, 18) + "..."
                  : outcome.bookmaker;

              return (
                <div
                  key={outcome.id}
                  className="text-xs truncate"
                  title={`${outcome.bookmaker} - ${
                    outcome.name
                  } @ ${outcome.odds.toFixed(2)}`}
                >
                  <span className="font-medium">{bookmaker}</span>
                  <span className="text-muted-foreground">
                    {" "}
                    - {outcome.name}
                  </span>
                  <span className="font-semibold">
                    {" "}
                    @ {outcome.odds.toFixed(2)}
                  </span>
                </div>
              );
            }
          )}
          {remainingCount > 0 && (
            <div className="text-xs text-muted-foreground italic">
              +{remainingCount} more...
            </div>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "bookmakers",
    header: () => null,
    cell: () => null,
    filterFn: (row, id, value) => {
      const outcomes = row.original.outcomes;
      return outcomes.some(
        (outcome: SurebetEvent["outcomes"][0]) => outcome.bookmaker === value
      );
    },
  },
  {
    accessorKey: "total_inverse_odds",
    header: "Arbitrage",
    cell: ({ row }: { row: any }) => {
      const total = row.getValue("total_inverse_odds") as number;
      // Show as percentage below 100% for easier understanding
      const arbPercentage = (total * 100).toFixed(2);
      return (
        <span
          className="text-xs text-muted-foreground"
          title={`Total inverse odds: ${total.toFixed(4)}`}
        >
          {arbPercentage}%
        </span>
      );
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }: { row: any }) => {
      const surebet = row.original as SurebetEvent;
      const outcomes = (surebet.outcomes || []) as SurebetEvent["outcomes"];

      // Pick the best odds per outcome name (e.g., Home/Draw/Away)
      const bestByOutcomeName = outcomes.reduce(
        (acc: Record<string, (typeof outcomes)[number]>, curr) => {
          const key = curr.name || "";
          if (!key) return acc;
          if (!acc[key] || curr.odds > acc[key].odds) {
            acc[key] = curr;
          }
          return acc;
        },
        {}
      );
      const bestOutcomes = Object.values(bestByOutcomeName);

      // Helper to ensure external URL is valid
      const toExternalUrl = (url?: string) => {
        if (!url) return undefined;
        try {
          // If it's relative, let URL throw and we ignore
          const u = new URL(url);
          return u.href;
        } catch {
          return undefined;
        }
      };

      // Collect best links (open up to 3 in new tabs)
      const bestLinks = bestOutcomes
        .map((o) => toExternalUrl(o.deep_link_url))
        .filter((u): u is string => Boolean(u));

      const [sheetOpen, setSheetOpen] = useState(false);

      const handleOpenBestLinks = (e: React.MouseEvent) => {
        e.preventDefault();
        // Open the best bookmaker pages for each outcome needed for the arb
        // Limit to 3 new tabs to avoid browser blocking
        bestLinks.slice(0, 3).forEach((href) => {
          window.open(href, "_blank", "noopener,noreferrer");
        });
      };

      return (
        <div className="flex items-center gap-2">
          {/* Go to Bets: open the top bookmaker pages for each outcome */}
          {bestLinks.length > 0 && (
            <Button
              onClick={handleOpenBestLinks}
              variant="default"
              size="sm"
              className="gap-2"
              title={`Opens ${Math.min(
                bestLinks.length,
                3
              )} tab(s) with the best bookmaker pages`}
            >
              <ExternalLink className="h-4 w-4" />
              Go to Bets
            </Button>
          )}

          {/* Additional Actions Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link
                  href={`/bet/${encodeURIComponent(surebet.event_id)}`}
                  className="w-full"
                >
                  View Details
                </Link>
              </DropdownMenuItem>
              {/* Controlled Sheet so it works inside DropdownMenu */}
              <DropdownMenuItem onClick={() => setSheetOpen(true)}>
                Calculate Stakes
              </DropdownMenuItem>
              <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
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
                    <SheetClose>
                      <Button variant="outline">Close</Button>
                    </SheetClose>
                  </SheetFooter>
                </SheetContent>
              </Sheet>
              {outcomes.map((outcome) => (
                <DropdownMenuItem key={outcome.id} asChild>
                  {toExternalUrl(outcome.deep_link_url) ? (
                    <Link
                      href={outcome.deep_link_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2"
                    >
                      <ExternalLink className="h-3 w-3" />
                      {outcome.bookmaker} - {outcome.name}
                    </Link>
                  ) : (
                    <span className="flex items-center gap-2 opacity-60 cursor-not-allowed">
                      <ExternalLink className="h-3 w-3" />
                      {outcome.bookmaker} - {outcome.name}
                    </span>
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      );
    },
  },
  {
    // Placeholder: this isn't a real column, but it's exported so TS won't complain when used below.
    accessorKey: "__internal__calculate_stakes_placeholder",
    header: () => null,
    cell: () => null,
  },
];

function CalculateStakesForm({
  outcomes,
}: {
  outcomes: SurebetEvent["outcomes"];
}) {
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
