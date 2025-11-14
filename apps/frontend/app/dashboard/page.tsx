"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  Timer,
  Percent,
  Database,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { io, Socket } from "socket.io-client";
import { toast } from "sonner";
import { RefreshButton } from "@/components/refresh-button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

import { DataTable } from "./data-table";
import { columns } from "./columns";

// TypeScript types matching backend schema
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

type SurebetsResponse = {
  surebets: SurebetEvent[];
  total_count: number;
  status: string;
};

export default function DashboardPage() {
  const [surebets, setSurebets] = useState<SurebetEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const fetchSurebets = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch("http://localhost:8000/api/v1/surebets");

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SurebetsResponse = await response.json();

      setSurebets(data.surebets);
      setLastRefresh(new Date());

      console.log(`✅ Fetched ${data.surebets.length} surebets from backend`);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch surebets";
      setError(errorMessage);
      console.error("❌ Error fetching surebets:", errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger scraper run via API
  const triggerScraper = async () => {
    try {
      toast.info("Triggering scraper run...");

      const response = await fetch("http://localhost:8000/api/v1/scraper/run", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Scraper triggered successfully:", data);
      toast.success(
        "Scraper run triggered successfully! Data will update automatically."
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to trigger scraper";
      console.error("❌ Error triggering scraper:", errorMessage);
      toast.error(`Failed to trigger scraper: ${errorMessage}`);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchSurebets();
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    console.log("🔌 Initializing WebSocket connection...");

    // Create socket connection
    const socket: Socket = io("http://localhost:8000", {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    // Connection event handlers
    socket.on("connect", () => {
      console.log("✅ WebSocket connected successfully");
      setIsConnected(true);
    });

    socket.on("disconnect", () => {
      console.log("⚠️  WebSocket disconnected");
      setIsConnected(false);
    });

    socket.on("connect_error", (error) => {
      console.error("❌ WebSocket connection error:", error);
      setIsConnected(false);
    });

    // Listen for new surebet updates from backend
    socket.on("new_surebets", (data: SurebetsResponse) => {
      console.log("📡 Received new surebets via WebSocket:", data);

      if (data && data.surebets) {
        setSurebets(data.surebets);
        setLastRefresh(new Date());
        console.log(
          `🔄 Updated dashboard with ${data.surebets.length} surebets`
        );
      }
    });

    // Cleanup on unmount
    return () => {
      console.log("🔌 Disconnecting WebSocket...");
      socket.disconnect();
    };
  }, []); // Empty dependency array - only run once on mount

  // Derive aggregate stats from live data
  const totalBets = surebets.length;
  const avgProfit =
    surebets.length > 0
      ? surebets.reduce((acc, sb) => acc + sb.profit_percentage, 0) /
        surebets.length
      : 0;
  const topProfit =
    surebets.length > 0
      ? Math.max(...surebets.map((s) => s.profit_percentage))
      : 0;
  const distinctSports = new Set(surebets.map((s) => s.sport)).size;

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="border-b bg-linear-to-r from-primary/20 via-secondary/10 to-accent/">
        <div className="container mx-auto px-4 py-8 flex flex-col items-center text-center gap-4">
          <div className="space-y-2 max-w-2xl mx-auto">
            <h1 className="text-3xl font-bold tracking-tight">
              Live Surebet Opportunities
            </h1>
            <p className="text-muted-foreground text-sm sm:text-base">
              Monitor real-time arbitrage edges across supported bookmakers. Use
              filters to refine and act quickly.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <RefreshButton onClick={triggerScraper} />
            {lastRefresh && (
              <span className="text-sm text-muted-foreground">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            {isConnected && (
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs text-muted-foreground">Live</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="container mx-auto px-4">
          <Alert variant="destructive" className="max-w-4xl mx-auto">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to fetch surebet data: {error}. Please make sure the
              backend is running and try again.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="container mx-auto px-4">
          <Card className="max-w-4xl mx-auto">
            <CardContent className="p-8 flex flex-col items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p className="text-muted-foreground">
                Loading surebet opportunities...
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stats Overview - Only show if data is loaded */}
      {!isLoading && !error && (
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
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
      )}

      {/* Data Table - Only show if data is loaded and no error */}
      {!isLoading && !error && (
        <div className="container mx-auto px-4 pb-12">
          <Card className="overflow-hidden max-w-7xl mx-auto">
            <CardContent className="p-6">
              {surebets.length > 0 ? (
                <DataTable columns={columns} data={surebets} />
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">
                    No surebet opportunities found at the moment.
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Data will appear here when profitable arbitrage
                    opportunities are detected.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
