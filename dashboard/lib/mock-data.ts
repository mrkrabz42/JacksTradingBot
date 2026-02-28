import type { AccountData, Position, PortfolioHistory, Trade, Order, MarketSnapshot } from "./types";

export const mockAccount: AccountData = {
  id: "mock-account",
  account_number: "PA0000000",
  status: "ACTIVE",
  equity: "10000.00",
  last_equity: "9950.00",
  buying_power: "8000.00",
  cash: "8000.00",
  portfolio_value: "10000.00",
  pattern_day_trader: false,
  trading_blocked: false,
  transfers_blocked: false,
  account_blocked: false,
  daytrade_count: 0,
  daytrading_buying_power: "0.00",
  long_market_value: "2000.00",
  short_market_value: "0.00",
};

export const mockPositions: Position[] = [];

export const mockPortfolioHistory: PortfolioHistory = {
  timestamp: [],
  equity: [],
  profit_loss: [],
  profit_loss_pct: [],
  base_value: 10000,
  timeframe: "1D",
};

export const mockTrades: Trade[] = [];

export const mockOrders: Order[] = [];

export const mockMarketSnapshot: MarketSnapshot = {
  quotes: {
    SPY: { ap: 502.50, as: 100, bp: 502.45, bs: 200, t: new Date().toISOString() },
    QQQ: { ap: 435.20, as: 150, bp: 435.15, bs: 300, t: new Date().toISOString() },
    DIA: { ap: 389.80, as: 50, bp: 389.75, bs: 100, t: new Date().toISOString() },
    IWM: { ap: 202.30, as: 80, bp: 202.25, bs: 120, t: new Date().toISOString() },
  },
};
