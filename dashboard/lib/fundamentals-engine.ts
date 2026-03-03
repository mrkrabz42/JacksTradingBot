/**
 * Fundamentals scoring engine.
 * 7 macro factors scored per instrument with asset-specific weights.
 */

import type { FredRawData, FredObservation } from "./fred";
import type { FundamentalFactor, FundamentalsData } from "./types";

// ── Factor names ────────────────────────────────────────────────────────────

const FACTOR_NAMES = [
  "Interest Rate Expectations",
  "Bond Yields (10Y & 2Y)",
  "DXY Strength",
  "Inflation (CPI/PCE)",
  "Employment (NFP/Unemployment)",
  "Risk Sentiment (VIX)",
  "Relative Economic Strength",
] as const;

type FactorName = (typeof FACTOR_NAMES)[number];

// ── Asset-specific weight matrix (1–5) ──────────────────────────────────────

const WEIGHT_MATRIX: Record<string, Record<FactorName, number>> = {
  NAS100_USD: {
    "Interest Rate Expectations": 5,
    "Bond Yields (10Y & 2Y)": 5,
    "DXY Strength": 3,
    "Inflation (CPI/PCE)": 4,
    "Employment (NFP/Unemployment)": 3,
    "Risk Sentiment (VIX)": 5,
    "Relative Economic Strength": 2,
  },
  SPX500_USD: {
    "Interest Rate Expectations": 4,
    "Bond Yields (10Y & 2Y)": 4,
    "DXY Strength": 3,
    "Inflation (CPI/PCE)": 3,
    "Employment (NFP/Unemployment)": 3,
    "Risk Sentiment (VIX)": 5,
    "Relative Economic Strength": 2,
  },
  EUR_USD: {
    "Interest Rate Expectations": 4,
    "Bond Yields (10Y & 2Y)": 3,
    "DXY Strength": 5,
    "Inflation (CPI/PCE)": 3,
    "Employment (NFP/Unemployment)": 2,
    "Risk Sentiment (VIX)": 2,
    "Relative Economic Strength": 5,
  },
  GBP_USD: {
    "Interest Rate Expectations": 4,
    "Bond Yields (10Y & 2Y)": 3,
    "DXY Strength": 5,
    "Inflation (CPI/PCE)": 3,
    "Employment (NFP/Unemployment)": 2,
    "Risk Sentiment (VIX)": 2,
    "Relative Economic Strength": 5,
  },
  XAU_USD: {
    "Interest Rate Expectations": 3,
    "Bond Yields (10Y & 2Y)": 4,
    "DXY Strength": 5,
    "Inflation (CPI/PCE)": 4,
    "Employment (NFP/Unemployment)": 2,
    "Risk Sentiment (VIX)": 3,
    "Relative Economic Strength": 2,
  },
  XAG_USD: {
    "Interest Rate Expectations": 2,
    "Bond Yields (10Y & 2Y)": 3,
    "DXY Strength": 5,
    "Inflation (CPI/PCE)": 3,
    "Employment (NFP/Unemployment)": 2,
    "Risk Sentiment (VIX)": 3,
    "Relative Economic Strength": 2,
  },
};

// ── Direction flip per asset ────────────────────────────────────────────────
// Each factor's "raw direction" is from a USD/risk perspective.
// The flip map converts it to be asset-specific.
//   +1 = same direction (rising factor = bullish for asset)
//   -1 = inverted (rising factor = bearish for asset)

const DIRECTION_FLIP: Record<string, Record<FactorName, 1 | -1>> = {
  // Indices: dovish/falling rates = bullish, falling yields = bullish, falling DXY = slight positive,
  //          cooling inflation = bullish, weak employment = bullish (more easing), low VIX = bullish
  NAS100_USD: {
    "Interest Rate Expectations": 1,  // dovish = bullish for NAS
    "Bond Yields (10Y & 2Y)": 1,     // falling yields = bullish
    "DXY Strength": -1,              // rising DXY = mildly bearish
    "Inflation (CPI/PCE)": 1,        // cooling CPI = bullish
    "Employment (NFP/Unemployment)": 1, // weak jobs = more easing = bullish
    "Risk Sentiment (VIX)": 1,       // low VIX = bullish
    "Relative Economic Strength": 1,  // US strong = bullish for US indices
  },
  SPX500_USD: {
    "Interest Rate Expectations": 1,
    "Bond Yields (10Y & 2Y)": 1,
    "DXY Strength": -1,
    "Inflation (CPI/PCE)": 1,
    "Employment (NFP/Unemployment)": 1,
    "Risk Sentiment (VIX)": 1,
    "Relative Economic Strength": 1,
  },
  // FX pairs: rising USD = bearish for EUR/USD and GBP/USD
  EUR_USD: {
    "Interest Rate Expectations": -1,  // hawkish USD = bearish EUR/USD
    "Bond Yields (10Y & 2Y)": -1,     // rising US yields = USD strength = bearish
    "DXY Strength": -1,               // rising DXY = bearish
    "Inflation (CPI/PCE)": -1,        // hot CPI = hawkish = USD strong = bearish
    "Employment (NFP/Unemployment)": -1,
    "Risk Sentiment (VIX)": 1,        // risk-on = bullish for EUR/USD
    "Relative Economic Strength": -1,  // US outperforming = bearish for EUR/USD
  },
  GBP_USD: {
    "Interest Rate Expectations": -1,
    "Bond Yields (10Y & 2Y)": -1,
    "DXY Strength": -1,
    "Inflation (CPI/PCE)": -1,
    "Employment (NFP/Unemployment)": -1,
    "Risk Sentiment (VIX)": 1,
    "Relative Economic Strength": -1,
  },
  // Gold/Silver: anti-USD, safe haven
  XAU_USD: {
    "Interest Rate Expectations": 1,   // dovish = bullish for gold
    "Bond Yields (10Y & 2Y)": 1,      // falling yields = bullish
    "DXY Strength": -1,               // rising DXY = bearish
    "Inflation (CPI/PCE)": -1,        // hot CPI = hawkish = bearish (real rates up)
    "Employment (NFP/Unemployment)": 1, // weak jobs = easing = bullish
    "Risk Sentiment (VIX)": -1,       // high VIX = safe haven demand = bullish (inverted)
    "Relative Economic Strength": -1,  // US strong = USD strong = bearish gold
  },
  XAG_USD: {
    "Interest Rate Expectations": 1,
    "Bond Yields (10Y & 2Y)": 1,
    "DXY Strength": -1,
    "Inflation (CPI/PCE)": -1,
    "Employment (NFP/Unemployment)": 1,
    "Risk Sentiment (VIX)": -1,
    "Relative Economic Strength": -1,
  },
};

// ── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Compute slope direction from an array of observations (newest first).
 * Returns +1 (rising), -1 (falling), 0 (flat).
 */
function slopeDirection(obs: FredObservation[], periods: number): 1 | 0 | -1 {
  if (obs.length < periods) return 0;
  // obs[0] is newest, obs[periods-1] is oldest in the window
  const newest = obs[0].value;
  const oldest = obs[periods - 1].value;
  const diff = newest - oldest;
  const threshold = Math.abs(oldest) * 0.005; // 0.5% change threshold for "flat"
  if (diff > threshold) return 1;  // rising
  if (diff < -threshold) return -1; // falling
  return 0;
}

function toState(dir: 1 | 0 | -1): "Bullish" | "Bearish" | "Neutral" {
  if (dir === 1) return "Bullish";
  if (dir === -1) return "Bearish";
  return "Neutral";
}

// ── Individual factor scorers ───────────────────────────────────────────────

function scoreInterestRates(dgs2: FredObservation[]): 1 | 0 | -1 {
  // Rising 2Y yields → hawkish → -1 for risk assets
  // Falling → dovish → +1 for risk assets
  const slope = slopeDirection(dgs2, 3);
  if (slope === 1) return -1;  // rising rates = hawkish
  if (slope === -1) return 1;  // falling rates = dovish
  return 0;
}

function scoreBondYields(dgs10: FredObservation[]): 1 | 0 | -1 {
  // Rising 10Y → -1 (higher borrowing costs)
  // Falling → +1
  const slope = slopeDirection(dgs10, 5);
  if (slope === 1) return -1;
  if (slope === -1) return 1;
  return 0;
}

function scoreDxy(eurUsdPrice: number | null, prevEurUsdPrice: number | null): 1 | 0 | -1 {
  // DXY ≈ inverse EUR/USD. Rising EUR/USD = falling DXY.
  if (eurUsdPrice == null || prevEurUsdPrice == null) return 0;
  const dxyChange = -(eurUsdPrice - prevEurUsdPrice) / prevEurUsdPrice;
  if (dxyChange > 0.001) return 1;   // DXY rising = USD strong
  if (dxyChange < -0.001) return -1;  // DXY falling = USD weak
  return 0;
}

function scoreInflation(cpi: FredObservation[]): 1 | 0 | -1 {
  // Compare latest CPI to 3 months ago
  if (cpi.length < 4) return 0;
  const latest = cpi[0].value;
  const threeMonthsAgo = cpi[3].value;
  const pctChange = (latest - threeMonthsAgo) / threeMonthsAgo;
  if (pctChange > 0.002) return -1;  // rising CPI = hawkish
  if (pctChange < -0.002) return 1;  // cooling CPI = easing
  return 0;
}

function scoreEmployment(unrate: FredObservation[], payems: FredObservation[]): 1 | 0 | -1 {
  // Strong labor = tightening expectations = -1
  // Weak labor = easing expectations = +1
  let signals = 0;

  if (unrate.length >= 2) {
    const urChange = unrate[0].value - unrate[1].value;
    if (urChange > 0.1) signals += 1;  // rising unemployment = weakening
    else if (urChange < -0.1) signals -= 1; // falling = strengthening
  }

  if (payems.length >= 2) {
    const nfpChange = payems[0].value - payems[1].value;
    if (nfpChange > 100) signals -= 1;  // strong NFP = tightening
    else if (nfpChange < 50) signals += 1; // weak NFP = easing
  }

  if (signals > 0) return 1;  // weak labor = easing
  if (signals < 0) return -1; // strong labor = tightening
  return 0;
}

function scoreVix(vix: FredObservation[]): 1 | 0 | -1 {
  if (vix.length < 2) return 0;
  const level = vix[0].value;
  const slope = slopeDirection(vix, 3);

  // VIX > 20 and rising → risk-off → -1
  // VIX < 20 and falling → risk-on → +1
  if (level > 20 && slope >= 0) return -1;
  if (level < 20 && slope <= 0) return 1;
  if (level > 25) return -1;
  if (level < 15) return 1;
  return 0;
}

function scoreRelativeStrength(usProd: FredObservation[], ukProd: FredObservation[]): 1 | 0 | -1 {
  // Compare growth rates of industrial production (US vs UK)
  if (usProd.length < 2 || ukProd.length < 2) return 0;
  const usGrowth = (usProd[0].value - usProd[1].value) / usProd[1].value;
  const ukGrowth = (ukProd[0].value - ukProd[1].value) / ukProd[1].value;
  const spread = usGrowth - ukGrowth;
  if (spread > 0.002) return 1;   // US outperforming
  if (spread < -0.002) return -1; // UK outperforming
  return 0;
}

// ── Main scoring function ───────────────────────────────────────────────────

export interface DxyPriceData {
  current: number | null;
  previous: number | null;
}

export function scoreFundamentals(
  symbol: string,
  rawData: FredRawData,
  dxy: DxyPriceData,
): FundamentalsData {
  const weights = WEIGHT_MATRIX[symbol];
  const flips = DIRECTION_FLIP[symbol];

  if (!weights || !flips) {
    throw new Error(`No weight/flip config for symbol: ${symbol}`);
  }

  // Compute raw directions for each factor
  const rawDirections: Record<FactorName, 1 | 0 | -1> = {
    "Interest Rate Expectations": scoreInterestRates(rawData.dgs2),
    "Bond Yields (10Y & 2Y)": scoreBondYields(rawData.dgs10),
    "DXY Strength": scoreDxy(dxy.current, dxy.previous),
    "Inflation (CPI/PCE)": scoreInflation(rawData.cpi),
    "Employment (NFP/Unemployment)": scoreEmployment(rawData.unrate, rawData.payems),
    "Risk Sentiment (VIX)": scoreVix(rawData.vix),
    "Relative Economic Strength": scoreRelativeStrength(rawData.usPmi, rawData.ukPmi),
  };

  // Build factor array with asset-specific flipping
  const factors: FundamentalFactor[] = FACTOR_NAMES.map((name) => {
    const rawDir = rawDirections[name];
    const flip = flips[name];
    const adjustedDir = (rawDir * flip) as 1 | 0 | -1;
    const weight = weights[name];

    return {
      name,
      state: toState(adjustedDir),
      direction: adjustedDir,
      weight,
      contribution: adjustedDir * weight,
      previousState: null, // could be populated from cache in future
    };
  });

  // Net score = sum of contributions
  const netScore = factors.reduce((sum, f) => sum + f.contribution, 0);
  const maxPossibleScore = factors.reduce((sum, f) => sum + f.weight, 0);

  // Map net score to bias label
  let netBias: FundamentalsData["netBias"];
  if (netScore > 10) netBias = "Strong Bullish";
  else if (netScore >= 4) netBias = "Moderate Bullish";
  else if (netScore >= -3) netBias = "Neutral";
  else if (netScore >= -10) netBias = "Moderate Bearish";
  else netBias = "Strong Bearish";

  // Normalize to 0-100 strength
  // Map from [-maxPossible, +maxPossible] to [0, 100]
  const strength = Math.round(((netScore + maxPossibleScore) / (2 * maxPossibleScore)) * 100);

  return {
    symbol,
    netBias,
    netScore,
    maxPossibleScore,
    strength: Math.max(0, Math.min(100, strength)),
    factors,
    updatedAt: new Date().toISOString(),
  };
}
