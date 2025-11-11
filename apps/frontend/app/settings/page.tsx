"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const [bookmakers, setBookmakers] = React.useState([
    { id: "bet365", name: "Bet365", enabled: true },
    { id: "betfair", name: "Betfair", enabled: true },
    { id: "williamhill", name: "William Hill", enabled: true },
    { id: "paddypower", name: "Paddy Power", enabled: false },
    { id: "ladbrokes", name: "Ladbrokes", enabled: true },
    { id: "unibet", name: "Unibet", enabled: false },
    { id: "888sport", name: "888Sport", enabled: true },
    { id: "betway", name: "Betway", enabled: true },
  ]);

  const [refreshInterval, setRefreshInterval] = React.useState("30");
  const [minProfit, setMinProfit] = React.useState("2.0");

  const handleToggleBookmaker = (id: string) => {
    setBookmakers((prev) =>
      prev.map((bookmaker) =>
        bookmaker.id === id
          ? { ...bookmaker, enabled: !bookmaker.enabled }
          : bookmaker
      )
    );
  };

  const handleSave = () => {
    console.log("Saving settings:", {
      bookmakers,
      refreshInterval,
      minProfit,
    });
    // Here you would typically send this to your backend API
    alert("Settings saved successfully!");
  };

  return (
    <div className="container mx-auto py-10">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Settings</h1>

        <div className="space-y-6">
          {/* Bookmaker Settings Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Bookmaker Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {bookmakers.map((bookmaker) => (
                  <div
                    key={bookmaker.id}
                    className="flex items-center justify-center gap-4"
                  >
                    <Label
                      htmlFor={bookmaker.id}
                      className="cursor-pointer text-center flex-1"
                    >
                      {bookmaker.name}
                    </Label>
                    <Switch
                      id={bookmaker.id}
                      checked={bookmaker.enabled}
                      onCheckedChange={() =>
                        handleToggleBookmaker(bookmaker.id)
                      }
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Data Settings Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Data Settings</CardTitle>
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
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <Button onClick={handleSave} className="w-full">
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  );
}
