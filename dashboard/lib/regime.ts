import type { Bar } from "@/lib/mss-pipeline";

// ── Config ─────────────────────────────────────────────────────────────
export interface RegimeConfig {
  adxPeriod: number;
  bbPeriod: number;
  bbStdDev: number;
  adxTrendThreshold: number;
  adxStrongTrendThreshold: number;
  bbWidthRangeThreshold: number;
  bbWidthTrendThreshold: number;
  vwapRangeBandPct: number;
  vwapTrendBandPct: number;
  lookbackBars: number;
}

export const DEFAULT_REGIME_CONFIG: RegimeConfig = {
  adxPeriod: 14,
  bbPeriod: 20,
  bbStdDev: 2,
  adxTrendThreshold: 25,
  adxStrongTrendThreshold: 35,
  bbWidthRangeThreshold: 0.01,
  bbWidthTrendThreshold: 0.03,
  vwapRangeBandPct: 0.003,
  vwapTrendBandPct: 0.01,
  lookbackBars: 20,
};

export type Regime = "TREND" | "RANGE" | "TRANSITION";

export interface RegimePoint {
  time: string;
  regime: Regime;
  adx: number;
  bbWidth: number;
  vwapDist: number;
}

// ── True Range helpers ─────────────────────────────────────────────────
function trueRange(h: number, l: number, prevClose: number): number {
  return Math.max(h - l, Math.abs(h - prevClose), Math.abs(l - prevClose));
}

// ── ADX ────────────────────────────────────────────────────────────────
export function computeADX(bars: Bar[], period = 14): number[] {
  const len = bars.length;
  if (len < period + 1) return new Array(len).fill(NaN);

  // +DM, -DM, TR arrays
  const plusDM: number[] = [0];
  const minusDM: number[] = [0];
  const tr: number[] = [bars[0].h - bars[0].l];

  for (let i = 1; i < len; i++) {
    const upMove = bars[i].h - bars[i - 1].h;
    const downMove = bars[i - 1].l - bars[i].l;
    plusDM.push(upMove > downMove && upMove > 0 ? upMove : 0);
    minusDM.push(downMove > upMove && downMove > 0 ? downMove : 0);
    tr.push(trueRange(bars[i].h, bars[i].l, bars[i - 1].c));
  }

  // Wilder smoothing
  const smooth = (arr: number[]): number[] => {
    const out: number[] = new Array(len).fill(NaN);
    let sum = 0;
    for (let i = 0; i < period; i++) sum += arr[i];
    out[period - 1] = sum;
    for (let i = period; i < len; i++) {
      out[i] = out[i - 1] - out[i - 1] / period + arr[i];
    }
    return out;
  };

  const smoothPDM = smooth(plusDM);
  const smoothMDM = smooth(minusDM);
  const smoothTR = smooth(tr);

  // +DI, -DI
  const plusDI: number[] = new Array(len).fill(NaN);
  const minusDI: number[] = new Array(len).fill(NaN);
  for (let i = period - 1; i < len; i++) {
    if (smoothTR[i] > 0) {
      plusDI[i] = (smoothPDM[i] / smoothTR[i]) * 100;
      minusDI[i] = (smoothMDM[i] / smoothTR[i]) * 100;
    } else {
      plusDI[i] = 0;
      minusDI[i] = 0;
    }
  }

  // DX → ADX
  const dx: number[] = new Array(len).fill(NaN);
  for (let i = period - 1; i < len; i++) {
    const sum = plusDI[i] + minusDI[i];
    dx[i] = sum > 0 ? (Math.abs(plusDI[i] - minusDI[i]) / sum) * 100 : 0;
  }

  const adx: number[] = new Array(len).fill(NaN);
  // First ADX = SMA of first `period` DX values
  const startIdx = 2 * period - 2;
  if (startIdx < len) {
    let dxSum = 0;
    for (let i = period - 1; i <= startIdx; i++) dxSum += (isNaN(dx[i]) ? 0 : dx[i]);
    adx[startIdx] = dxSum / period;
    for (let i = startIdx + 1; i < len; i++) {
      adx[i] = (adx[i - 1] * (period - 1) + (isNaN(dx[i]) ? 0 : dx[i])) / period;
    }
  }

  return adx;
}

// ── Bollinger Band Width ───────────────────────────────────────────────
export function computeBBWidth(bars: Bar[], period = 20, stdDev = 2): number[] {
  const len = bars.length;
  const result: number[] = new Array(len).fill(NaN);
  const closes = bars.map((b) => b.c);

  for (let i = period - 1; i < len; i++) {
    const window = closes.slice(i - period + 1, i + 1);
    const mean = window.reduce((a, b) => a + b, 0) / period;
    const variance = window.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
    const sd = Math.sqrt(variance);
    const upper = mean + stdDev * sd;
    const lower = mean - stdDev * sd;
    result[i] = mean > 0 ? (upper - lower) / mean : 0;
  }

  return result;
}

// ── VWAP ───────────────────────────────────────────────────────────────
export function computeVWAP(bars: Bar[]): number[] {
  let cumPV = 0;
  let cumVol = 0;
  return bars.map((b) => {
    cumPV += b.c * b.v;
    cumVol += b.v;
    return cumVol > 0 ? cumPV / cumVol : b.c;
  });
}

// ── Single-bar classification ──────────────────────────────────────────
export function classifyRegime(
  close: number,
  adx: number,
  bbWidth: number,
  vwap: number,
  config: RegimeConfig = DEFAULT_REGIME_CONFIG,
): Regime {
  const distVwapPct = vwap !== 0 ? Math.abs(close - vwap) / vwap : 0;

  const isAdxTrending = adx >= config.adxTrendThreshold;
  const isVolLow = bbWidth <= config.bbWidthRangeThreshold;
  const isVolHigh = bbWidth >= config.bbWidthTrendThreshold;
  const nearVwap = distVwapPct <= config.vwapRangeBandPct;
  const farFromVwap = distVwapPct >= config.vwapTrendBandPct;

  if (!isAdxTrending && isVolLow && nearVwap) return "RANGE";
  if (isAdxTrending && (isVolHigh || farFromVwap)) return "TREND";
  return "TRANSITION";
}

// ── Full series with smoothing ─────────────────────────────────────────
export function computeRegimeSeries(
  bars: Bar[],
  config: RegimeConfig = DEFAULT_REGIME_CONFIG,
): RegimePoint[] {
  const adxArr = computeADX(bars, config.adxPeriod);
  const bbArr = computeBBWidth(bars, config.bbPeriod, config.bbStdDev);
  const vwapArr = computeVWAP(bars);

  // Raw classification
  const raw: Regime[] = bars.map((b, i) => {
    const a = adxArr[i];
    const bb = bbArr[i];
    const v = vwapArr[i];
    if (isNaN(a) || isNaN(bb)) return "TRANSITION";
    return classifyRegime(b.c, a, bb, v, config);
  });

  // Majority-vote smoothing
  const smoothed: Regime[] = raw.map((_, i) => {
    const start = Math.max(0, i - config.lookbackBars + 1);
    const window = raw.slice(start, i + 1);
    const counts: Record<string, number> = { TREND: 0, RANGE: 0, TRANSITION: 0 };
    for (const r of window) counts[r]++;
    let best: Regime = "TRANSITION";
    let bestCount = 0;
    for (const [k, v] of Object.entries(counts)) {
      if (v > bestCount) { best = k as Regime; bestCount = v; }
    }
    return best;
  });

  return bars.map((b, i) => ({
    time: b.t,
    regime: smoothed[i],
    adx: isNaN(adxArr[i]) ? 0 : Math.round(adxArr[i] * 100) / 100,
    bbWidth: isNaN(bbArr[i]) ? 0 : Math.round(bbArr[i] * 10000) / 10000,
    vwapDist: vwapArr[i] !== 0
      ? Math.round((Math.abs(b.c - vwapArr[i]) / vwapArr[i]) * 10000) / 10000
      : 0,
  }));
}
