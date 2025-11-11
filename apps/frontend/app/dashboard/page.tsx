import { TrendingUp, Timer, Percent, Database } from "lucide-react";
import { RefreshButton } from "@/components/refresh-button";
import { Card, CardContent } from "@/components/ui/card";

import { DataTable } from "./data-table";
import { mockData } from "./mock-data";
import { columns } from "./columns";

export default function DashboardPage() {
  // Derive simple aggregate stats from mock data
  const totalBets = mockData.length;
  const avgProfit =
    mockData.reduce((acc, sb) => acc + sb.profit, 0) / (mockData.length || 1);
  const topProfit = Math.max(...mockData.map((s) => s.profit));
  const distinctSports = new Set(mockData.map((s) => s.sport)).size;

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="border-b bg-linear-to-r from-primary/20 via-secondary/10 to-accent/20">
        <div className="container mx-auto px-4 py-8 flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">
              Live Surebet Opportunities
            </h1>
            <p className="text-muted-foreground max-w-xl text-sm sm:text-base">
              Monitor real-time arbitrage edges across supported bookmakers. Use
              filters to refine and act quickly.
            </p>
          </div>
          <RefreshButton />
        </div>
      </div>

      {/* Stats Overview */}
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card/60 backdrop-blur">
            <CardContent className="p-4 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" /> Total Bets
              </div>
              <span className="text-2xl font-semibold">{totalBets}</span>
            </CardContent>
          </Card>
          <Card className="bg-card/60 backdrop-blur">
            <CardContent className="p-4 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Percent className="h-4 w-4" /> Avg Profit
              </div>
              <span className="text-2xl font-semibold">
                {avgProfit.toFixed(2)}%
              </span>
            </CardContent>
          </Card>
          <Card className="bg-card/60 backdrop-blur">
            <CardContent className="p-4 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Timer className="h-4 w-4" /> Top Profit
              </div>
              <span className="text-2xl font-semibold">
                {topProfit.toFixed(2)}%
              </span>
            </CardContent>
          </Card>
          <Card className="bg-card/60 backdrop-blur">
            <CardContent className="p-4 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Database className="h-4 w-4" /> Sports
              </div>
              <span className="text-2xl font-semibold">{distinctSports}</span>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Data Table */}
      <div className="container mx-auto px-4 pb-12">
        <Card className="overflow-hidden">
          <CardContent className="p-6">
            <DataTable columns={columns} data={mockData} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
