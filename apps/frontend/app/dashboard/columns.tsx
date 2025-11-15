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
import React from "react";

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
                <Link href={`/bet/${surebet.event_id}`} className="w-full">
                  View Details
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() =>
                  console.log("Calculate stakes:", surebet.event_id)
                }
              >
                Calculate Stakes
              </DropdownMenuItem>
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
];
