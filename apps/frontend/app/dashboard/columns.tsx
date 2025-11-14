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
      return (
        <div className="flex flex-col">
          <span className="font-medium">{event}</span>
          <span className="text-sm text-muted-foreground">{sport}</span>
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
      return (
        <div className="flex flex-col gap-1">
          {outcomes.map(
            (outcome: SurebetEvent["outcomes"][0], index: number) => (
              <div key={outcome.id} className="text-sm">
                <span className="font-medium">{outcome.bookmaker}</span>
                {" - "}
                <span className="text-muted-foreground">{outcome.name}</span>
                {" @ "}
                <span className="font-semibold">{outcome.odds.toFixed(2)}</span>
              </div>
            )
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
    header: "Inverse Odds",
    cell: ({ row }: { row: any }) => {
      const total = row.getValue("total_inverse_odds") as number;
      return (
        <span className="text-sm text-muted-foreground">
          {total.toFixed(4)}
        </span>
      );
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }: { row: any }) => {
      const surebet = row.original as SurebetEvent;
      const firstOutcome = surebet.outcomes[0];

      return (
        <div className="flex items-center gap-2">
          {/* Go to Bet Button */}
          {firstOutcome && firstOutcome.deep_link_url && (
            <Link
              href={firstOutcome.deep_link_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex"
            >
              <Button variant="default" size="sm" className="gap-2">
                <ExternalLink className="h-4 w-4" />
                Go to Bet
              </Button>
            </Link>
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
              <DropdownMenuItem
                onClick={() => console.log("View details:", surebet.event_id)}
              >
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() =>
                  console.log("Calculate stakes:", surebet.event_id)
                }
              >
                Calculate Stakes
              </DropdownMenuItem>
              {surebet.outcomes.map((outcome) => (
                <DropdownMenuItem key={outcome.id} asChild>
                  <Link
                    href={outcome.deep_link_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2"
                  >
                    <ExternalLink className="h-3 w-3" />
                    {outcome.bookmaker} - {outcome.name}
                  </Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      );
    },
  },
];
