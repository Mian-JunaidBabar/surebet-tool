"use client";

import { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Surebet } from "./mock-data";

/**
 * Format a date to show time elapsed (e.g., "5 minutes ago")
 */
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds} second${diffInSeconds !== 1 ? "s" : ""} ago`;
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes !== 1 ? "s" : ""} ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours !== 1 ? "s" : ""} ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} day${diffInDays !== 1 ? "s" : ""} ago`;
}

export const columns: ColumnDef<Surebet>[] = [
  {
    accessorKey: "profit",
    header: "Profit",
    cell: ({ row }: { row: any }) => {
      const profit = row.getValue("profit") as number;
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
      const outcomes = row.getValue("outcomes") as Surebet["outcomes"];
      return (
        <div className="flex flex-col gap-1">
          {outcomes.map((outcome, index) => (
            <div key={index} className="text-sm">
              <span className="font-medium">{outcome.bookmaker}</span>
              {" - "}
              <span className="text-muted-foreground">{outcome.name}</span>
              {" @ "}
              <span className="font-semibold">{outcome.odds.toFixed(2)}</span>
            </div>
          ))}
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
      return outcomes.some((outcome) => outcome.bookmaker === value);
    },
  },
  {
    accessorKey: "discoveredAt",
    header: "Discovered",
    cell: ({ row }: { row: any }) => {
      const date = row.getValue("discoveredAt") as Date;
      return (
        <span className="text-sm text-muted-foreground">
          {formatTimeAgo(date)}
        </span>
      );
    },
    filterFn: (row, id, value) => {
      const date = row.getValue(id) as Date;
      return date.getTime() >= value;
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }: { row: any }) => {
      const surebet = row.original;

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => console.log("View details:", surebet.id)}
            >
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => console.log("Calculate stakes:", surebet.id)}
            >
              Calculate Stakes
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
