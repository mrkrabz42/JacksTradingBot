export interface AccountData {
  id: string;
  account_number: string;
  status: string;
  equity: string;
  last_equity: string;
  buying_power: string;
  cash: string;
  portfolio_value: string;
  pattern_day_trader: boolean;
  trading_blocked: boolean;
  transfers_blocked: boolean;
  account_blocked: boolean;
  daytrade_count: number;
  daytrading_buying_power: string;
  long_market_value: string;
  short_market_value: string;
}

export interface Position {
  asset_id: string;
  symbol: string;
  exchange: string;
  asset_class: string;
  avg_entry_price: string;
  qty: string;
  side: string;
  market_value: string;
  cost_basis: string;
  unrealized_pl: string;
  unrealized_plpc: string;
  current_price: string;
  lastday_price: string;
  change_today: string;
}

export interface PortfolioHistory {
  timestamp: number[];
  equity: number[];
  profit_loss: number[];
  profit_loss_pct: number[];
  base_value: number;
  timeframe: string;
}

export interface Trade {
  id: string;
  activity_type: string;
  symbol: string;
  side: string;
  qty: string;
  price: string;
  cum_qty: string;
  order_id: string;
  transaction_time: string;
  type: string;
}

export interface Order {
  id: string;
  symbol: string;
  side: string;
  type: string;
  qty: string;
  filled_qty: string;
  status: string;
  created_at: string;
  updated_at: string;
  submitted_at: string;
  limit_price: string | null;
  stop_price: string | null;
  time_in_force: string;
  order_class: string;
}

export interface Quote {
  ap: number;
  as: number;
  bp: number;
  bs: number;
  t: string;
}

export interface MarketSnapshot {
  quotes: Record<string, Quote>;
}

// Timezone & Market types

export type TimezoneKey = "london" | "new_york" | "tokyo" | "hong_kong" | "sydney";

export interface TimezoneOption {
  key: TimezoneKey;
  label: string;
  flag: string;
  iana: string;
  abbr: string;
  exchange: string;
}

export interface MarketSession {
  open: string; // "HH:mm"
  close: string; // "HH:mm"
}

export interface MarketConfig {
  exchangeName: string;
  timezone: string; // IANA timezone
  sessions: MarketSession[];
  extendedHours?: { preMarket: MarketSession; afterHours: MarketSession };
  weekends: number[]; // day-of-week (0=Sun, 6=Sat)
}

export type MarketStatus = "open" | "pre_market" | "after_hours" | "closed";

export interface MarketStatusResult {
  status: MarketStatus;
  label: string;
  countdown: string;
  dotColor: string;
}

// Navigation
export interface NavItem {
  key: string;
  label: string;
  icon: string;
  href: string;
}

// Globe
export interface GlobeMarker {
  location: [number, number];
  size: number;
  exchangeKey: TimezoneKey;
  label: string;
}

// Bot Status / Session Liquidity
export interface SessionLevel {
  session: string;
  label: string;
  high: number | null;
  high_time: string | null;
  low: number | null;
  low_time: string | null;
  bar_count: number;
}

export interface DailyLevel {
  pdh: number | null;
  pdh_time: string | null;
  pdh_session: string | null;
  pdl: number | null;
  pdl_time: string | null;
  pdl_session: string | null;
  date: string;
}

export interface SessionProgress {
  session: string;
  label: string;
  progress_pct: number;
  elapsed_min: number;
  remaining_min: number;
  start_utc: string | null;
  end_utc: string | null;
}

export interface BotStatus {
  timestamp: string;
  symbol: string;
  current_session: SessionProgress;
  sessions: SessionLevel[];
  daily: DailyLevel;
  is_holiday?: boolean;
  data_date?: string;
}
