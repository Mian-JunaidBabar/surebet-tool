"use client";

import * as React from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Filter, X } from "lucide-react";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
}

export function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [sportFilter, setSportFilter] = React.useState<string>("");
  const [minProfit, setMinProfit] = React.useState<string>("");
  const [maxProfit, setMaxProfit] = React.useState<string>("");
  const [bookmakerFilter, setBookmakerFilter] = React.useState<string>("");
  const [timeFilter, setTimeFilter] = React.useState<string>("");

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onColumnFiltersChange: setColumnFilters,
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      columnFilters,
    },
  });

  // Get unique sports and bookmakers for filter options
  const sports = React.useMemo(() => {
    const uniqueSports = new Set(data.map((item: any) => item.sport));
    return Array.from(uniqueSports).sort();
  }, [data]);

  const bookmakers = React.useMemo(() => {
    const uniqueBookmakers = new Set(
      data.flatMap((item: any) =>
        item.outcomes.map((outcome: any) => outcome.bookmaker)
      )
    );
    return Array.from(uniqueBookmakers).sort();
  }, [data]);

  // Apply custom filters
  React.useEffect(() => {
    const filters: ColumnFiltersState = [];

    // Event filter (existing)
    const eventFilter = table.getColumn("event")?.getFilterValue() as string;
    if (eventFilter) {
      filters.push({ id: "event", value: eventFilter });
    }

    // Sport filter
    if (sportFilter) {
      table.getColumn("sport")?.setFilterValue(sportFilter);
      filters.push({ id: "sport", value: sportFilter });
    } else {
      table.getColumn("sport")?.setFilterValue(undefined);
    }

    // Profit range filter
    if (minProfit || maxProfit) {
      const min = minProfit ? parseFloat(minProfit) : 0;
      const max = maxProfit ? parseFloat(maxProfit) : Infinity;
      table.getColumn("profit")?.setFilterValue([min, max]);
      filters.push({ id: "profit", value: [min, max] });
    } else {
      table.getColumn("profit")?.setFilterValue(undefined);
    }

    // Bookmaker filter
    if (bookmakerFilter) {
      table.getColumn("bookmakers")?.setFilterValue(bookmakerFilter);
      filters.push({ id: "bookmakers", value: bookmakerFilter });
    } else {
      table.getColumn("bookmakers")?.setFilterValue(undefined);
    }

    // Time filter
    if (timeFilter) {
      const now = Date.now();
      let timeThreshold = now;
      switch (timeFilter) {
        case "1h":
          timeThreshold = now - 60 * 60 * 1000;
          break;
        case "6h":
          timeThreshold = now - 6 * 60 * 60 * 1000;
          break;
        case "24h":
          timeThreshold = now - 24 * 60 * 60 * 1000;
          break;
      }
      table.getColumn("discoveredAt")?.setFilterValue(timeThreshold);
      filters.push({ id: "discoveredAt", value: timeThreshold });
    } else {
      table.getColumn("discoveredAt")?.setFilterValue(undefined);
    }

    setColumnFilters(filters);
  }, [sportFilter, minProfit, maxProfit, bookmakerFilter, timeFilter, table]);

  const clearFilters = () => {
    setSportFilter("");
    setMinProfit("");
    setMaxProfit("");
    setBookmakerFilter("");
    setTimeFilter("");
    table.getColumn("event")?.setFilterValue("");
    setColumnFilters([]);
  };

  const hasActiveFilters =
    sportFilter ||
    minProfit ||
    maxProfit ||
    bookmakerFilter ||
    timeFilter ||
    (table.getColumn("event")?.getFilterValue() as string);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span className="text-sm font-medium">Filters</span>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="h-6 px-2 text-xs"
            >
              <X className="h-3 w-3 mr-1" />
              Clear all
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Event Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Event</label>
            <Input
              placeholder="Filter events..."
              value={
                (table.getColumn("event")?.getFilterValue() as string) ?? ""
              }
              onChange={(event) =>
                table.getColumn("event")?.setFilterValue(event.target.value)
              }
              className="h-9"
            />
          </div>

          {/* Sport Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Sport</label>
            <Select value={sportFilter} onValueChange={setSportFilter}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="All sports" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All sports</SelectItem>
                {sports.map((sport) => (
                  <SelectItem key={sport} value={sport}>
                    {sport}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Profit Range Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Profit Range (%)</label>
            <div className="flex gap-2">
              <Input
                placeholder="Min"
                type="number"
                step="0.1"
                value={minProfit}
                onChange={(e) => setMinProfit(e.target.value)}
                className="h-9"
              />
              <Input
                placeholder="Max"
                type="number"
                step="0.1"
                value={maxProfit}
                onChange={(e) => setMaxProfit(e.target.value)}
                className="h-9"
              />
            </div>
          </div>

          {/* Bookmaker Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Bookmaker</label>
            <Select value={bookmakerFilter} onValueChange={setBookmakerFilter}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="All bookmakers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All bookmakers</SelectItem>
                {bookmakers.map((bookmaker) => (
                  <SelectItem key={bookmaker} value={bookmaker}>
                    {bookmaker}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Time Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Discovered</label>
            <Select value={timeFilter} onValueChange={setTimeFilter}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Any time" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Any time</SelectItem>
                <SelectItem value="1h">Last hour</SelectItem>
                <SelectItem value="6h">Last 6 hours</SelectItem>
                <SelectItem value="24h">Last 24 hours</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2">
            {sportFilter && (
              <Badge variant="secondary" className="gap-1">
                Sport: {sportFilter}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => setSportFilter("")}
                />
              </Badge>
            )}
            {(minProfit || maxProfit) && (
              <Badge variant="secondary" className="gap-1">
                Profit: {minProfit || "0"}% - {maxProfit || "∞"}%
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => {
                    setMinProfit("");
                    setMaxProfit("");
                  }}
                />
              </Badge>
            )}
            {bookmakerFilter && (
              <Badge variant="secondary" className="gap-1">
                Bookmaker: {bookmakerFilter}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => setBookmakerFilter("")}
                />
              </Badge>
            )}
            {timeFilter && (
              <Badge variant="secondary" className="gap-1">
                Time:{" "}
                {timeFilter === "1h"
                  ? "Last hour"
                  : timeFilter === "6h"
                  ? "Last 6 hours"
                  : "Last 24 hours"}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => setTimeFilter("")}
                />
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-end space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
