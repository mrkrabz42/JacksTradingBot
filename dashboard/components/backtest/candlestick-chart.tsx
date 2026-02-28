"use client";

import { useRef, useEffect } from "react";
import {
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type SeriesMarker,
  type Time,
  type ISeriesMarkersPluginApi,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
} from "lightweight-charts";
import type { Bar, CP, MSSEvent, SweepEvent, LiquidityPool } from "@/lib/mss-pipeline";

interface CandlestickChartProps {
  bars: Bar[];
  swings: CP[];
  mssEvents: MSSEvent[];
  sweepEvents: SweepEvent[];
  liquidityPools: LiquidityPool[];
  liveBars?: Bar[];
  scrollToTimestamp?: string | null;
}

function toChartTime(isoString: string): Time {
  return Math.floor(new Date(isoString).getTime() / 1000) as Time;
}

export function CandlestickChart({
  bars,
  swings,
  mssEvents,
  sweepEvents,
  liquidityPools,
  liveBars,
  scrollToTimestamp,
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const disposedRef = useRef(false);

  // Create chart once on mount
  useEffect(() => {
    if (!containerRef.current) return;
    disposedRef.current = false;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      crosshair: {
        vertLine: { color: "rgba(236,72,153,0.3)", labelBackgroundColor: "#ec4899" },
        horzLine: { color: "rgba(236,72,153,0.3)", labelBackgroundColor: "#ec4899" },
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.1)",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.1)",
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
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    // Resize observer
    const ro = new ResizeObserver(entries => {
      if (disposedRef.current) return;
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          chart.applyOptions({ width, height });
        }
      }
    });
    ro.observe(containerRef.current);

    return () => {
      disposedRef.current = true;
      ro.disconnect();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      markersRef.current = null;
      chart.remove();
    };
  }, []);

  // Update candle + volume data when bars or liveBars change
  useEffect(() => {
    const candleSeries = candleSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    if (!candleSeries || !volumeSeries || disposedRef.current) return;

    const allBars = liveBars ? [...bars, ...liveBars] : bars;

    // Deduplicate by timestamp (live bars may overlap)
    const seen = new Set<string>();
    const uniqueBars: Bar[] = [];
    for (const b of allBars) {
      if (!seen.has(b.t)) {
        seen.add(b.t);
        uniqueBars.push(b);
      }
    }

    const candleData: CandlestickData[] = uniqueBars.map(b => ({
      time: toChartTime(b.t),
      open: b.o,
      high: b.h,
      low: b.l,
      close: b.c,
    }));
    candleSeries.setData(candleData);

    const volData: HistogramData[] = uniqueBars.map(b => ({
      time: toChartTime(b.t),
      value: b.v,
      color: b.c >= b.o ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)",
    }));
    volumeSeries.setData(volData);
  }, [bars, liveBars]);

  // Update markers when overlay data changes
  useEffect(() => {
    const candleSeries = candleSeriesRef.current;
    if (!candleSeries || disposedRef.current) return;

    const markers: SeriesMarker<Time>[] = [];

    for (const cp of swings) {
      markers.push({
        time: toChartTime(cp.time),
        position: cp.type === "HIGH" ? "aboveBar" : "belowBar",
        color: cp.type === "HIGH" ? "#f472b6" : "#60a5fa",
        shape: "circle",
        text: cp.type === "HIGH" ? "SH" : "SL",
      });
    }

    for (const mss of mssEvents) {
      markers.push({
        time: toChartTime(mss.timestamp),
        position: mss.direction === "BULL" ? "belowBar" : "aboveBar",
        color: mss.direction === "BULL" ? "#10b981" : "#ef4444",
        shape: mss.direction === "BULL" ? "arrowUp" : "arrowDown",
        text: `${Math.round(mss.displacement_quality * 100)}%`,
      });
    }

    for (const sweep of sweepEvents) {
      markers.push({
        time: toChartTime(sweep.timestamp),
        position: sweep.direction === "BULL" ? "belowBar" : "aboveBar",
        color: "#eab308",
        shape: "square",
        text: "SWEEP",
      });
    }

    markers.sort((a, b) => (a.time as number) - (b.time as number));

    // Replace existing markers plugin
    if (markersRef.current) {
      markersRef.current.setMarkers([]);
    }
    markersRef.current = createSeriesMarkers(candleSeries, markers);
  }, [swings, mssEvents, sweepEvents]);

  // Update liquidity pool price lines
  useEffect(() => {
    const candleSeries = candleSeriesRef.current;
    if (!candleSeries || disposedRef.current) return;

    // Remove old price lines
    for (const line of candleSeries.priceLines()) {
      candleSeries.removePriceLine(line);
    }

    for (const pool of liquidityPools) {
      candleSeries.createPriceLine({
        price: pool.price,
        color: pool.type === "HIGH" ? "rgba(244,114,182,0.4)" : "rgba(96,165,250,0.4)",
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `LIQ ${pool.type === "HIGH" ? "H" : "L"} (${pool.count})`,
      });
    }
  }, [liquidityPools]);

  // Fit content once after initial data load
  useEffect(() => {
    if (!chartRef.current || disposedRef.current || bars.length === 0) return;
    chartRef.current.timeScale().fitContent();
  }, [bars.length > 0]); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll to timestamp
  useEffect(() => {
    if (!scrollToTimestamp || !chartRef.current || disposedRef.current) return;
    const time = toChartTime(scrollToTimestamp);
    const from = (time as number) - 600;
    const to = (time as number) + 600;
    chartRef.current.timeScale().setVisibleRange({
      from: from as Time,
      to: to as Time,
    });
  }, [scrollToTimestamp]);

  return (
    <div ref={containerRef} className="w-full h-full min-h-[300px]" />
  );
}
