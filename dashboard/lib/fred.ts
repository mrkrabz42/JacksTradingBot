/**
 * FRED (Federal Reserve Economic Data) API client.
 * Free API — register at https://fred.stlouisfed.org/docs/api/api_key.html
 */

const FRED_BASE = "https://api.stlouisfed.org/fred";

function getApiKey(): string {
  const key = process.env.FRED_API_KEY;
  if (!key) throw new Error("Missing FRED_API_KEY env var");
  return key;
}

// ── Series IDs ──────────────────────────────────────────────────────────────

export const FRED_SERIES = {
  DGS10: "DGS10",           // 10-Year Treasury Constant Maturity Rate (daily)
  DGS2: "DGS2",             // 2-Year Treasury Constant Maturity Rate (daily)
  CPIAUCSL: "CPIAUCSL",     // CPI for All Urban Consumers (monthly)
  PCEPILFE: "PCEPILFE",     // Core PCE Price Index (monthly)
  UNRATE: "UNRATE",         // Unemployment Rate (monthly)
  PAYEMS: "PAYEMS",         // Nonfarm Payrolls (monthly)
  CES0500000003: "CES0500000003", // Average Hourly Earnings (monthly)
  VIXCLS: "VIXCLS",         // CBOE VIX Close (daily)
  INDPRO: "INDPRO",         // US Industrial Production Index (monthly, PMI proxy)
  GBRPROINDMISMEI: "GBRPROINDMISMEI", // UK Industrial Production via OECD (monthly)
  BAMLH0A0HYM2: "BAMLH0A0HYM2", // ICE BofA US High Yield OAS (daily, credit spread)
  T10Y3M: "T10Y3M",         // 10Y minus 3M Treasury spread (daily, yield curve)
} as const;

export type FredSeriesId = keyof typeof FRED_SERIES;

// Daily series get 1h TTL, monthly series get 6h TTL
const DAILY_SERIES = new Set<string>(["DGS10", "DGS2", "VIXCLS", "BAMLH0A0HYM2", "T10Y3M"]);

const CACHE_TTL_DAILY = 60 * 60 * 1000;    // 1 hour
const CACHE_TTL_MONTHLY = 6 * 60 * 60 * 1000; // 6 hours

// ── In-memory cache ─────────────────────────────────────────────────────────

interface CacheEntry {
  data: FredObservation[];
  fetchedAt: number;
}

const cache = new Map<string, CacheEntry>();

export interface FredObservation {
  date: string;   // YYYY-MM-DD
  value: number;
}

// ── Fetch observations ──────────────────────────────────────────────────────

/**
 * Fetch recent observations for a FRED series.
 * Returns newest observations first (reversed for easy trend analysis).
 */
export async function fetchSeries(
  seriesId: string,
  limit = 12,
): Promise<FredObservation[]> {
  const ttl = DAILY_SERIES.has(seriesId) ? CACHE_TTL_DAILY : CACHE_TTL_MONTHLY;
  const cacheKey = `${seriesId}:${limit}`;

  // Check cache
  const cached = cache.get(cacheKey);
  if (cached && Date.now() - cached.fetchedAt < ttl) {
    return cached.data;
  }

  const apiKey = getApiKey();
  const url = `${FRED_BASE}/series/observations?series_id=${seriesId}&api_key=${apiKey}&file_type=json&sort_order=desc&limit=${limit}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`FRED API error ${res.status} for ${seriesId}: ${body}`);
  }

  const json = await res.json();
  const observations: FredObservation[] = [];

  for (const obs of json.observations ?? []) {
    // FRED returns "." for missing/unavailable values
    if (obs.value === "." || obs.value == null) continue;
    observations.push({
      date: obs.date,
      value: parseFloat(obs.value),
    });
  }

  cache.set(cacheKey, { data: observations, fetchedAt: Date.now() });
  return observations;
}

// ── Bulk fetch ──────────────────────────────────────────────────────────────

export interface FredRawData {
  dgs10: FredObservation[];
  dgs2: FredObservation[];
  cpi: FredObservation[];
  corePce: FredObservation[];
  unrate: FredObservation[];
  payems: FredObservation[];
  wages: FredObservation[];
  vix: FredObservation[];
  usPmi: FredObservation[];
  ukPmi: FredObservation[];
  hyOas: FredObservation[];
  t10y3m: FredObservation[];
}

/**
 * Fetch all FRED series needed for fundamentals scoring.
 * Runs all fetches in parallel.
 */
export async function fetchAllFredData(): Promise<FredRawData> {
  const [dgs10, dgs2, cpi, corePce, unrate, payems, wages, vix, usPmi, ukPmi, hyOas, t10y3m] =
    await Promise.all([
      fetchSeries(FRED_SERIES.DGS10, 10),
      fetchSeries(FRED_SERIES.DGS2, 10),
      fetchSeries(FRED_SERIES.CPIAUCSL, 6),
      fetchSeries(FRED_SERIES.PCEPILFE, 6),
      fetchSeries(FRED_SERIES.UNRATE, 6),
      fetchSeries(FRED_SERIES.PAYEMS, 6),
      fetchSeries(FRED_SERIES.CES0500000003, 6),
      fetchSeries(FRED_SERIES.VIXCLS, 10),
      fetchSeries(FRED_SERIES.INDPRO, 4),
      fetchSeries(FRED_SERIES.GBRPROINDMISMEI, 4),
      fetchSeries(FRED_SERIES.BAMLH0A0HYM2, 10),
      fetchSeries(FRED_SERIES.T10Y3M, 10),
    ]);

  return { dgs10, dgs2, cpi, corePce, unrate, payems, wages, vix, usPmi, ukPmi, hyOas, t10y3m };
}
