export const REFRESH_INTERVALS = {
  ACCOUNT: 30_000,
  POSITIONS: 30_000,
  ORDERS: 30_000,
  TRADES: 60_000,
  MARKET_SNAPSHOT: 60_000,
  PORTFOLIO_HISTORY: 300_000,
  BOT_STATUS: 10_000,
  ALERTS: 10_000,
} as const;

export const TIMEZONE = "Europe/London";

export const INDEX_SYMBOLS = ["SPY", "QQQ", "DIA", "IWM"] as const;

export const RISK_PARAMS = {
  MAX_RISK_PER_TRADE: 0.02,
  MAX_POSITIONS: 5,
  DAILY_LOSS_LIMIT: 0.05,
} as const;

import type { TimezoneKey, TimezoneOption, MarketConfig, NavItem, GlobeMarker } from "./types";

export const LOCALSTORAGE_KEY_TZ = "mr10krabs_timezone";

export const TIMEZONE_OPTIONS: TimezoneOption[] = [
  { key: "london", label: "London", flag: "\u{1F1EC}\u{1F1E7}", iana: "Europe/London", abbr: "GMT/BST", exchange: "LSE" },
  { key: "new_york", label: "New York", flag: "\u{1F1FA}\u{1F1F8}", iana: "America/New_York", abbr: "ET", exchange: "NYSE/NASDAQ" },
  { key: "tokyo", label: "Tokyo", flag: "\u{1F1EF}\u{1F1F5}", iana: "Asia/Tokyo", abbr: "JST", exchange: "TSE" },
  { key: "hong_kong", label: "Hong Kong", flag: "\u{1F1ED}\u{1F1F0}", iana: "Asia/Hong_Kong", abbr: "HKT", exchange: "HKEX" },
  { key: "sydney", label: "Sydney", flag: "\u{1F1E6}\u{1F1FA}", iana: "Australia/Sydney", abbr: "AEST", exchange: "ASX" },
];

export const MARKET_HOURS: Record<TimezoneKey, MarketConfig> = {
  london: {
    exchangeName: "LSE",
    timezone: "Europe/London",
    sessions: [{ open: "08:00", close: "16:30" }],
    weekends: [0, 6],
  },
  new_york: {
    exchangeName: "NYSE/NASDAQ",
    timezone: "America/New_York",
    sessions: [{ open: "09:30", close: "16:00" }],
    extendedHours: {
      preMarket: { open: "04:00", close: "09:30" },
      afterHours: { open: "16:00", close: "20:00" },
    },
    weekends: [0, 6],
  },
  tokyo: {
    exchangeName: "TSE",
    timezone: "Asia/Tokyo",
    sessions: [
      { open: "09:00", close: "11:30" },
      { open: "12:30", close: "15:00" },
    ],
    weekends: [0, 6],
  },
  hong_kong: {
    exchangeName: "HKEX",
    timezone: "Asia/Hong_Kong",
    sessions: [
      { open: "09:30", close: "12:00" },
      { open: "13:00", close: "16:00" },
    ],
    weekends: [0, 6],
  },
  sydney: {
    exchangeName: "ASX",
    timezone: "Australia/Sydney",
    sessions: [{ open: "10:00", close: "16:00" }],
    weekends: [0, 6],
  },
};

export const NAV_ITEMS: NavItem[] = [
  { key: "dashboard", label: "Dashboard", icon: "LayoutDashboard", href: "/" },
  { key: "positions", label: "Positions", icon: "Briefcase", href: "/positions" },
  { key: "trades", label: "Trades", icon: "ArrowLeftRight", href: "/trades" },
  { key: "strategy", label: "Strategy", icon: "Brain", href: "/strategy" },
  { key: "bot", label: "Bot Status", icon: "Activity", href: "/bot" },
  { key: "market-hours", label: "Market Hours", icon: "Globe", href: "/market-hours" },
  { key: "backtest", label: "Backtest", icon: "CandlestickChart", href: "/backtest" },
  { key: "alerts", label: "Alerts", icon: "Bell", href: "/alerts" },
  { key: "settings", label: "Settings", icon: "Settings", href: "/settings" },
];

export const GLOBE_MARKERS: GlobeMarker[] = [
  { location: [51.5074, -0.1278], size: 0.08, exchangeKey: "london", label: "LSE" },
  { location: [40.7128, -74.006], size: 0.1, exchangeKey: "new_york", label: "NYSE" },
  { location: [35.6762, 139.6503], size: 0.08, exchangeKey: "tokyo", label: "TSE" },
  { location: [22.3193, 114.1694], size: 0.07, exchangeKey: "hong_kong", label: "HKEX" },
  { location: [-33.8688, 151.2093], size: 0.07, exchangeKey: "sydney", label: "ASX" },
];

export const LOCALSTORAGE_KEY_SIDEBAR = "mr10krabs_sidebar_collapsed";
