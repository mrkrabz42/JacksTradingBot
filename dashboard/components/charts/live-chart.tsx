"use client";

import { useRef, useEffect } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type Time,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
  CrosshairMode,
} from "lightweight-charts";

export interface BarData {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}

interface LiveChartProps {
  bars: BarData[];
  livePrice?: number;
  symbol: string;
  onCrosshairMove?: (data: { time: string; open: number; high: number; low: number; close: number; volume: number } | null) => void;
}

function toChartTime(isoString: string): Time {
  return Math.floor(new Date(isoString).getTime() / 1000) as Time;
}

export function LiveChart({ bars, livePrice, symbol, onCrosshairMove }: LiveChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const disposedRef = useRef(false);

  // Create chart on mount
  useEffect(() => {
    if (!containerRef.current) return;
    disposedRef.current = false;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "inherit",
        fontSize: 12,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.03)" },
        horzLines: { color: "rgba(255,255,255,0.03)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "rgba(100,150,255,0.3)", width: 1, labelBackgroundColor: "#3b82f6" },
        horzLine: { color: "rgba(100,150,255,0.3)", width: 1, labelBackgroundColor: "#3b82f6" },
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.08)",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 10,
        barSpacing: 6,
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.08)",
        scaleMargins: { top: 0.05, bottom: 0.2 },
      },
    });

    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderUpColor: "#10b981",
      borderDownColor: "#ef4444",
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });
    candleSeriesRef.current = candleSeries;

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // Crosshair move handler for OHLC display
    chart.subscribeCrosshairMove((param) => {
      if (!onCrosshairMove) return;
      if (!param.time || !param.seriesData) {
        onCrosshairMove(null);
        return;
      }
      const candle = param.seriesData.get(candleSeries) as CandlestickData | undefined;
      const vol = param.seriesData.get(volumeSeries) as HistogramData | undefined;
      if (candle) {
        onCrosshairMove({
          time: new Date((param.time as number) * 1000).toISOString(),
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
          volume: vol?.value ?? 0,
        });
      }
    });

    // Resize
    const ro = new ResizeObserver((entries) => {
      if (disposedRef.current) return;
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) chart.applyOptions({ width, height });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      disposedRef.current = true;
      ro.disconnect();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      chart.remove();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Update data
  useEffect(() => {
    const cs = candleSeriesRef.current;
    const vs = volumeSeriesRef.current;
    if (!cs || !vs || disposedRef.current || bars.length === 0) return;

    const seen = new Set<string>();
    const unique: BarData[] = [];
    for (const b of bars) {
      if (!seen.has(b.t)) { seen.add(b.t); unique.push(b); }
    }

    cs.setData(unique.map((b) => ({
      time: toChartTime(b.t),
      open: b.o, high: b.h, low: b.l, close: b.c,
    })));

    vs.setData(unique.map((b) => ({
      time: toChartTime(b.t),
      value: b.v,
      color: b.c >= b.o ? "rgba(16,185,129,0.25)" : "rgba(239,68,68,0.25)",
    })));
  }, [bars]);

  // Live price line
  useEffect(() => {
    const cs = candleSeriesRef.current;
    if (!cs || !livePrice || disposedRef.current) return;

    // Remove old price lines
    for (const line of cs.priceLines()) cs.removePriceLine(line);

    cs.createPriceLine({
      price: livePrice,
      color: "#3b82f6",
      lineWidth: 1,
      lineStyle: 0,
      axisLabelVisible: true,
      title: symbol,
    });
  }, [livePrice, symbol]);

  // Fit content on first load
  const fitted = useRef(false);
  useEffect(() => {
    if (fitted.current || !chartRef.current || bars.length === 0) return;
    chartRef.current.timeScale().fitContent();
    fitted.current = true;
  }, [bars.length > 0]); // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={containerRef} className="w-full h-full" />;
}
