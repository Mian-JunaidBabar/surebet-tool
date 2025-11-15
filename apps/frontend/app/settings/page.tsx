"use client";

import * as React from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Trash2, Plus, Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

// TypeScript types
type ScraperTarget = {
  id: number;
  url: string;
  name: string;
  is_active: boolean;
};

type Settings = {
  refresh_interval: string;
  min_profit_threshold: string;
  raptor_mini_enabled?: string;
};

export default function SettingsPage() {
  // Settings state
  const [refreshInterval, setRefreshInterval] = React.useState("30");
  const [minProfit, setMinProfit] = React.useState("2.0");
  const [raptorEnabled, setRaptorEnabled] = React.useState(false);

  // Scraper targets state
  const [scraperTargets, setScraperTargets] = React.useState<ScraperTarget[]>(
    []
  );
  const [newTargetName, setNewTargetName] = React.useState("");
  const [newTargetUrl, setNewTargetUrl] = React.useState("");

  // UI state
  const [isLoading, setIsLoading] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Fetch settings and scraper targets on mount
  React.useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch both settings and scraper targets in parallel
      const [settingsResponse, targetsResponse] = await Promise.all([
        fetch("http://localhost:8000/api/v1/settings"),
        fetch("http://localhost:8000/api/v1/scraper/targets"),
      ]);

      if (!settingsResponse.ok || !targetsResponse.ok) {
        throw new Error("Failed to fetch data from backend");
      }

      const settingsData = await settingsResponse.json();
      const targetsData = await targetsResponse.json();

      // Update settings state
      if (settingsData.settings) {
        setRefreshInterval(settingsData.settings.refresh_interval || "30");
        setMinProfit(settingsData.settings.min_profit_threshold || "2.0");
        const raptorRaw = settingsData.settings.raptor_mini_enabled || "false";
        setRaptorEnabled(String(raptorRaw).toLowerCase() === "true");
      }

      // Update scraper targets state
      if (targetsData.targets) {
        setScraperTargets(targetsData.targets);
      }

      console.log("✅ Fetched settings and targets successfully");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch data";
      setError(errorMessage);
      console.error("❌ Error fetching data:", errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Save general settings
  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      setError(null);

      const response = await fetch("http://localhost:8000/api/v1/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          settings: {
            refresh_interval: refreshInterval,
            min_profit_threshold: minProfit,
            raptor_mini_enabled: raptorEnabled ? "true" : "false",
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save settings");
      }

      console.log("✅ Settings saved successfully");
      toast.success("Settings saved successfully!");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save settings";
      setError(errorMessage);
      console.error("❌ Error saving settings:", errorMessage);
      toast.error(`Failed to save settings: ${errorMessage}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Toggle scraper target active status
  const handleToggleTarget = async (
    targetId: number,
    currentStatus: boolean
  ) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/scraper/targets/${targetId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            is_active: !currentStatus,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update target");
      }

      console.log(`✅ Target ${targetId} updated successfully`);
      toast.success(
        `Target ${!currentStatus ? "enabled" : "disabled"} successfully`
      );

      // Re-fetch targets to update UI
      await fetchData();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to update target";
      console.error("❌ Error updating target:", errorMessage);
      toast.error(`Failed to update target: ${errorMessage}`);
    }
  };

  // Delete scraper target
  const handleDeleteTarget = async (targetId: number) => {
    if (!confirm("Are you sure you want to delete this scraper target?")) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/scraper/targets/${targetId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete target");
      }

      console.log(`✅ Target ${targetId} deleted successfully`);
      toast.success("Target deleted successfully");

      // Re-fetch targets to update UI
      await fetchData();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to delete target";
      console.error("❌ Error deleting target:", errorMessage);
      toast.error(`Failed to delete target: ${errorMessage}`);
    }
  };

  // Add new scraper target
  const handleAddTarget = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newTargetName.trim() || !newTargetUrl.trim()) {
      toast.error("Please fill in both name and URL");
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/scraper/targets",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: newTargetName,
            url: newTargetUrl,
            is_active: true,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to add target");
      }

      console.log("✅ New target added successfully");
      toast.success("New scraper target added successfully!");

      // Clear form
      setNewTargetName("");
      setNewTargetUrl("");

      // Re-fetch targets to update UI
      await fetchData();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to add target";
      console.error("❌ Error adding target:", errorMessage);
      toast.error(`Failed to add target: ${errorMessage}`);
    }
  };

  return (
    <div className="container mx-auto py-10">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Settings</h1>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {isLoading ? (
          <Card>
            <CardContent className="p-8 flex flex-col items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p className="text-muted-foreground">Loading settings...</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Scraper Targets Management Card */}
            <Card>
              <CardHeader>
                <CardTitle>Scraper Targets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Targets Table */}
                  <div className="border rounded-md">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>URL</TableHead>
                          <TableHead className="text-center">Active</TableHead>
                          <TableHead className="text-center">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {scraperTargets.length === 0 ? (
                          <TableRow>
                            <TableCell
                              colSpan={4}
                              className="text-center text-muted-foreground"
                            >
                              No scraper targets configured yet
                            </TableCell>
                          </TableRow>
                        ) : (
                          scraperTargets.map((target) => (
                            <TableRow key={target.id}>
                              <TableCell className="font-medium">
                                {target.name}
                              </TableCell>
                              <TableCell className="text-sm text-muted-foreground max-w-md truncate">
                                {target.url}
                              </TableCell>
                              <TableCell className="text-center">
                                <Switch
                                  checked={target.is_active}
                                  onCheckedChange={() =>
                                    handleToggleTarget(
                                      target.id,
                                      target.is_active
                                    )
                                  }
                                />
                              </TableCell>
                              <TableCell className="text-center">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleDeleteTarget(target.id)}
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Add New Target Form */}
                  <form onSubmit={handleAddTarget} className="space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label htmlFor="new-target-name">Target Name</Label>
                        <Input
                          id="new-target-name"
                          placeholder="e.g., BetExplorer Premier League"
                          value={newTargetName}
                          onChange={(e) => setNewTargetName(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="new-target-url">Target URL</Label>
                        <Input
                          id="new-target-url"
                          placeholder="https://..."
                          value={newTargetUrl}
                          onChange={(e) => setNewTargetUrl(e.target.value)}
                        />
                      </div>
                    </div>
                    <Button type="submit" className="w-full">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Scraper Target
                    </Button>
                  </form>
                </div>
              </CardContent>
            </Card>

            {/* General Settings Card */}
            <Card>
              <CardHeader>
                <CardTitle>General Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="refresh-interval">
                      Refresh Interval (seconds)
                    </Label>
                    <Input
                      id="refresh-interval"
                      type="number"
                      value={refreshInterval}
                      onChange={(e) => setRefreshInterval(e.target.value)}
                      placeholder="30"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="min-profit">
                      Minimum Profit Threshold (%)
                    </Label>
                    <Input
                      id="min-profit"
                      type="number"
                      step="0.1"
                      value={minProfit}
                      onChange={(e) => setMinProfit(e.target.value)}
                      placeholder="2.0"
                    />
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <Label htmlFor="raptor-mini">
                        Enable Raptor mini (Preview)
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        When enabled, all connected clients will see the Raptor
                        mini preview.
                      </p>
                    </div>
                    <div>
                      <Switch
                        id="raptor-mini"
                        checked={raptorEnabled}
                        onCheckedChange={(val) =>
                          setRaptorEnabled(Boolean(val))
                        }
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Save Settings Button */}
            <Button
              onClick={handleSaveSettings}
              className="w-full"
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save General Settings"
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
