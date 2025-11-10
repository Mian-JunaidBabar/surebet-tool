/**
 * Mock Data and TypeScript Types for Surebet Dashboard
 */

export type Surebet = {
  id: string;
  profit: number;
  event: string;
  sport: string;
  outcomes: Array<{
    bookmaker: string;
    name: string;
    odds: number;
  }>;
  discoveredAt: Date;
};

export const mockData: Surebet[] = [
  {
    id: "sb-001",
    profit: 3.24,
    event: "Arsenal vs. Tottenham Hotspur",
    sport: "Football",
    outcomes: [
      { bookmaker: "Bet365", name: "Arsenal Win", odds: 2.15 },
      { bookmaker: "William Hill", name: "Draw", odds: 3.8 },
      { bookmaker: "Betfair", name: "Tottenham Win", odds: 3.5 },
    ],
    discoveredAt: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
  },
  {
    id: "sb-002",
    profit: 2.87,
    event: "Manchester City vs. Liverpool",
    sport: "Football",
    outcomes: [
      { bookmaker: "Paddy Power", name: "Man City Win", odds: 1.95 },
      { bookmaker: "Betfair", name: "Draw", odds: 3.9 },
      { bookmaker: "Bet365", name: "Liverpool Win", odds: 4.2 },
    ],
    discoveredAt: new Date(Date.now() - 12 * 60 * 1000), // 12 minutes ago
  },
  {
    id: "sb-003",
    profit: 4.15,
    event: "Los Angeles Lakers vs. Golden State Warriors",
    sport: "Basketball",
    outcomes: [
      { bookmaker: "DraftKings", name: "Lakers Win", odds: 2.05 },
      { bookmaker: "FanDuel", name: "Warriors Win", odds: 1.88 },
    ],
    discoveredAt: new Date(Date.now() - 8 * 60 * 1000), // 8 minutes ago
  },
  {
    id: "sb-004",
    profit: 1.92,
    event: "Rafael Nadal vs. Novak Djokovic",
    sport: "Tennis",
    outcomes: [
      { bookmaker: "Bet365", name: "Nadal Win", odds: 2.3 },
      { bookmaker: "Unibet", name: "Djokovic Win", odds: 1.75 },
    ],
    discoveredAt: new Date(Date.now() - 20 * 60 * 1000), // 20 minutes ago
  },
  {
    id: "sb-005",
    profit: 3.67,
    event: "Boston Bruins vs. Toronto Maple Leafs",
    sport: "Ice Hockey",
    outcomes: [
      { bookmaker: "Betway", name: "Bruins Win", odds: 2.1 },
      { bookmaker: "888Sport", name: "Draw", odds: 4.0 },
      { bookmaker: "William Hill", name: "Maple Leafs Win", odds: 3.3 },
    ],
    discoveredAt: new Date(Date.now() - 3 * 60 * 1000), // 3 minutes ago
  },
  {
    id: "sb-006",
    profit: 2.45,
    event: "New York Yankees vs. Boston Red Sox",
    sport: "Baseball",
    outcomes: [
      { bookmaker: "FanDuel", name: "Yankees Win", odds: 1.91 },
      { bookmaker: "BetMGM", name: "Red Sox Win", odds: 2.15 },
    ],
    discoveredAt: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
  },
  {
    id: "sb-007",
    profit: 5.23,
    event: "Real Madrid vs. Barcelona",
    sport: "Football",
    outcomes: [
      { bookmaker: "Betfair", name: "Real Madrid Win", odds: 2.4 },
      { bookmaker: "Ladbrokes", name: "Draw", odds: 3.5 },
      { bookmaker: "Bet365", name: "Barcelona Win", odds: 2.95 },
    ],
    discoveredAt: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
  },
  {
    id: "sb-008",
    profit: 1.78,
    event: "Milwaukee Bucks vs. Brooklyn Nets",
    sport: "Basketball",
    outcomes: [
      { bookmaker: "Caesars", name: "Bucks Win", odds: 1.72 },
      { bookmaker: "PointsBet", name: "Nets Win", odds: 2.25 },
    ],
    discoveredAt: new Date(Date.now() - 25 * 60 * 1000), // 25 minutes ago
  },
  {
    id: "sb-009",
    profit: 3.89,
    event: "Chelsea vs. Manchester United",
    sport: "Football",
    outcomes: [
      { bookmaker: "William Hill", name: "Chelsea Win", odds: 2.2 },
      { bookmaker: "Betway", name: "Draw", odds: 3.6 },
      { bookmaker: "Paddy Power", name: "Man United Win", odds: 3.4 },
    ],
    discoveredAt: new Date(Date.now() - 7 * 60 * 1000), // 7 minutes ago
  },
  {
    id: "sb-010",
    profit: 2.56,
    event: "Tampa Bay Lightning vs. Florida Panthers",
    sport: "Ice Hockey",
    outcomes: [
      { bookmaker: "DraftKings", name: "Lightning Win", odds: 1.95 },
      { bookmaker: "FanDuel", name: "Draw", odds: 4.1 },
      { bookmaker: "BetMGM", name: "Panthers Win", odds: 3.8 },
    ],
    discoveredAt: new Date(Date.now() - 10 * 60 * 1000), // 10 minutes ago
  },
  {
    id: "sb-011",
    profit: 4.32,
    event: "Paris Saint-Germain vs. Bayern Munich",
    sport: "Football",
    outcomes: [
      { bookmaker: "Bet365", name: "PSG Win", odds: 2.6 },
      { bookmaker: "Unibet", name: "Draw", odds: 3.3 },
      { bookmaker: "Betfair", name: "Bayern Win", odds: 2.75 },
    ],
    discoveredAt: new Date(Date.now() - 1 * 60 * 1000), // 1 minute ago
  },
  {
    id: "sb-012",
    profit: 2.18,
    event: "Serena Williams vs. Naomi Osaka",
    sport: "Tennis",
    outcomes: [
      { bookmaker: "Ladbrokes", name: "Williams Win", odds: 2.1 },
      { bookmaker: "888Sport", name: "Osaka Win", odds: 1.85 },
    ],
    discoveredAt: new Date(Date.now() - 18 * 60 * 1000), // 18 minutes ago
  },
];
