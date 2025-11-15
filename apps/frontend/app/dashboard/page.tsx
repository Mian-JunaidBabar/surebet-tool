"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  Timer,
  Percent,
  Database,
  AlertCircle,
  Loader2,
  RefreshCw,
  Activity,
  ExternalLink,
} from "lucide-react";
import { io, Socket } from "socket.io-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

type ApiUsage = {
  used: string;
  remaining: string;
};

export default function DashboardPage() {
  const [surebets, setSurebets] = useState<SurebetEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isScraperLoading, setIsScraperLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scraperError, setScraperError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [apiUsage, setApiUsage] = useState<ApiUsage | null>(null);

  // Handler for the "Fetch Live Odds" button
  const handleFetchOdds = async () => {
    try {
      setIsLoading(true);
      setError(null);

      toast.info("Fetching live odds from The Odds API...");

      const response = await fetch("http://localhost:8000/api/v1/odds/fetch", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update API usage from the response
      if (data.usage) {
        setApiUsage(data.usage);
      }

      // Update surebets (will also be updated via WebSocket)
      if (data.surebets) {
        setSurebets(data.surebets);
        setLastRefresh(new Date());
      }

      // Show success toast with usage info
      const usedRequests = data.usage?.used || "0";
      toast.success(
        `Successfully fetched odds! Used ${usedRequests} API request${
          usedRequests !== "1" ? "s" : ""
        }.`
      );

      console.log(`✅ Fetched ${data.surebets?.length || 0} surebets from API`);
      console.log(
        `📊 API Usage - Used: ${data.usage?.used}, Remaining: ${data.usage?.remaining}`
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch odds";
      setError(errorMessage);
      console.error("❌ Error fetching odds:", errorMessage);
      toast.error(`Failed to fetch odds: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for triggering the scraper (unified - now uses stealth by default)
  const handleRunScraper = async () => {
    try {
      setIsScraperLoading(true);
      setError(null);

      toast.info("🕵️ Running scraper with anti-detection measures...");

      const response = await fetch("http://localhost:8000/api/v1/scraper/run", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      toast.success(
        "✅ Scraper activated! Data will be updated automatically."
      );
      console.log("✅ Scraper triggered successfully:", data);

      // Poll for results after a few seconds to provide feedback
      setTimeout(async () => {
        try {
          const checkResponse = await fetch(
            "http://localhost:8000/api/v1/surebets"
          );
          const checkData = await checkResponse.json();
          if (checkData.total_count === 0) {
            const errorMsg =
              "⚠️ Scraper completed but found no events. Sites may be blocking or have no live odds available.";
            setScraperError(errorMsg);
            toast.warning(errorMsg);
          } else {
            setScraperError(null);
          }
        } catch (e) {
          console.log("Could not check scraper results:", e);
        }
      }, 10000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to trigger scraper";
      console.error("❌ Error triggering scraper:", errorMessage);
      toast.error(`Failed to trigger scraper: ${errorMessage}`);
    } finally {
      setIsScraperLoading(false);
    }
  };

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

    // Listen for new surebet updates from backend (handle both payload shapes)
    socket.on("new_surebets", (data: any) => {
      console.log("📡 Received new surebets via WebSocket:", data);

      // Case 1: backend emitted a plain array
      if (Array.isArray(data)) {
        setSurebets(data as SurebetEvent[]);
        setLastRefresh(new Date());
        console.log(`🔄 Updated dashboard with ${data.length} surebets`);
        toast.success(`Updated with ${data.length} new surebet opportunities!`);
        return;
      }

      // Case 2: backend emitted an object { surebets: [...], total_count, timestamp }
      if (data && Array.isArray(data.surebets)) {
        setSurebets(data.surebets as SurebetEvent[]);
        setLastRefresh(new Date());
        console.log(
          `🔄 Updated dashboard with ${data.surebets.length} surebets`
        );
        toast.success(
          `Updated with ${data.surebets.length} new surebet opportunities!`
        );
      }
    });

    // Cleanup on unmount
    return () => {
      console.log("🔌 Disconnecting WebSocket...");
      socket.disconnect();
    };
  }, []); // Empty dependency array - only run once on mount

  // Fetch persisted surebets on initial load so navigation doesn't clear the table
  useEffect(() => {
    const loadSurebets = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const res = await fetch("http://localhost:8000/api/v1/surebets", {
          cache: "no-store",
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: SurebetsResponse = await res.json();
        setSurebets(data.surebets || []);
        setLastRefresh(new Date());
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Failed to load data";
        console.error("Failed to load surebets:", msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };
    loadSurebets();
  }, []);

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
      {/* Header Section with Fetch Button */}
      <div className="border-b bg-gradient-to-r from-primary/20 via-secondary/10 to-accent/10">
        <div className="container mx-auto px-4 py-8 flex flex-col items-center text-center gap-6">
          <div className="space-y-2 max-w-2xl mx-auto">
            <h1 className="text-3xl font-bold tracking-tight">
              Live Surebet Opportunities
            </h1>
            <p className="text-muted-foreground text-sm sm:text-base">
              Click "Fetch Live Odds" to retrieve real-time arbitrage
              opportunities from The Odds API
            </p>
          </div>

          {/* Fetch Button and API Usage Card */}
          <Card className="w-full max-w-3xl">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2 justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Data Sources
                </div>
                {apiUsage && (
                  <a
                    href="https://the-odds-api.com/account/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-500 hover:text-blue-700 underline flex items-center gap-1"
                  >
                    View API Dashboard
                    <svg
                      className="w-3 h-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-4">
                {/* The Odds API Section */}
                <div className="flex flex-col sm:flex-row items-center gap-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
                  <div className="flex-1 space-y-2">
                    <h3 className="font-semibold text-sm">
                      The Odds API (Recommended)
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Reliable, fast, and always up-to-date odds from 40+
                      bookmakers
                    </p>
                  </div>
                  <Button
                    onClick={handleFetchOdds}
                    disabled={isLoading}
                    size="lg"
                    className="w-full sm:w-auto"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Fetching...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Fetch from API
                      </>
                    )}
                  </Button>
                </div>

                {/* Scraper Section - Unified */}
                <div className="flex flex-col sm:flex-row items-center gap-4 p-4 bg-purple-50 dark:bg-purple-950 rounded-lg border-2 border-purple-200 dark:border-purple-800">
                  <div className="flex-1 space-y-2">
                    <h3 className="font-semibold text-sm flex items-center gap-2">
                      🕵️ Web Scraper (Stealth Mode)
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Advanced scraping with anti-detection, proxies, and human
                      behavior simulation
                    </p>
                    <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1">
                      <li>Bypasses Cloudflare & bot detection</li>
                      <li>Residential proxy support (optional)</li>
                      <li>Human-like mouse movements & scrolling</li>
                      <li>Production-grade selectors</li>
                    </ul>
                  </div>
                  <Button
                    onClick={handleRunScraper}
                    disabled={isScraperLoading}
                    size="lg"
                    variant="default"
                    className="w-full sm:w-auto bg-purple-600 hover:bg-purple-700"
                  >
                    {isScraperLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Running...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Update Live Odds
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* API Usage Display */}
              {apiUsage && (
                <div className="flex flex-col gap-2 p-4 bg-muted rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">API Credits</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold">
                        {apiUsage.used} /{" "}
                        {parseInt(apiUsage.used) + parseInt(apiUsage.remaining)}
                      </span>
                      <a
                        href="https://dash.the-odds-api.com/api-subscriptions"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors flex items-center gap-1"
                      >
                        Dashboard
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${
                          (parseInt(apiUsage.used) /
                            (parseInt(apiUsage.used) +
                              parseInt(apiUsage.remaining))) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Used: {apiUsage.used}</span>
                    <span>Remaining: {apiUsage.remaining}</span>
                  </div>
                </div>
              )}

              {/* Last Refresh and Connection Status */}
              <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
                {lastRefresh && (
                  <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
                )}
                {isConnected && (
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    <span>Live WebSocket Connected</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
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

      {/* Scraper Error Banner */}
      {scraperError && !error && (
        <div className="container mx-auto px-4">
          <Alert className="max-w-4xl mx-auto bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800">
            <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <AlertDescription className="text-amber-800 dark:text-amber-200">
              {scraperError}
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
