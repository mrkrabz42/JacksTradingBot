"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import createGlobe from "cobe";
import { GLOBE_MARKERS } from "@/lib/constants";
import { getMarketStatus } from "@/lib/market-utils";
import type { MarketStatus } from "@/lib/types";

function statusToColor(status: MarketStatus): [number, number, number] {
  switch (status) {
    case "open": return [0.063, 0.725, 0.506]; // green
    case "pre_market":
    case "after_hours": return [1, 0.647, 0]; // orange
    default: return [0.937, 0.267, 0.267]; // red (#ef4444)
  }
}

export function GlobeView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerStart = useRef<{ x: number; y: number } | null>(null);
  const phiRef = useRef(0);
  const thetaRef = useRef(0.3);
  const dragPhiStart = useRef(0);
  const dragThetaStart = useRef(0.3);
  const [markers, setMarkers] = useState<
    { location: [number, number]; size: number; color: [number, number, number] }[]
  >([]);

  // Update marker colors every 10s
  useEffect(() => {
    const update = () => {
      const now = new Date();
      setMarkers(
        GLOBE_MARKERS.map((m) => {
          const result = getMarketStatus(now, m.exchangeKey);
          return {
            location: m.location,
            size: m.size,
            color: statusToColor(result.status),
          };
        })
      );
    };
    update();
    const interval = setInterval(update, 10_000);
    return () => clearInterval(interval);
  }, []);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    pointerStart.current = { x: e.clientX, y: e.clientY };
    dragPhiStart.current = phiRef.current;
    dragThetaStart.current = thetaRef.current;
    if (canvasRef.current) canvasRef.current.style.cursor = "grabbing";
  }, []);

  const onPointerUp = useCallback(() => {
    pointerStart.current = null;
    if (canvasRef.current) canvasRef.current.style.cursor = "grab";
  }, []);

  const onPointerOut = useCallback(() => {
    pointerStart.current = null;
    if (canvasRef.current) canvasRef.current.style.cursor = "grab";
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (pointerStart.current !== null) {
      const dx = e.clientX - pointerStart.current.x;
      const dy = e.clientY - pointerStart.current.y;
      phiRef.current = dragPhiStart.current + dx / 100;
      // Clamp theta between -PI/2 and PI/2 to prevent flipping
      thetaRef.current = Math.max(
        -Math.PI / 2,
        Math.min(Math.PI / 2, dragThetaStart.current + dy / 100)
      );
    }
  }, []);

  useEffect(() => {
    if (!canvasRef.current) return;

    let width = 0;

    const onResize = () => {
      if (canvasRef.current) {
        width = canvasRef.current.offsetWidth;
      }
    };
    window.addEventListener("resize", onResize);
    onResize();

    const globe = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: width * 2,
      height: width * 2,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 6,
      baseColor: [0.1, 0.1, 0.15],
      markerColor: [1, 0.412, 0.706], // pink fallback
      glowColor: [0.06, 0.06, 0.1],
      markers: markers.length > 0
        ? markers
        : GLOBE_MARKERS.map((m) => ({ location: m.location, size: m.size })),
      onRender: (state) => {
        // Auto-rotate when not dragging
        if (pointerStart.current === null) {
          phiRef.current += 0.003;
        }
        state.phi = phiRef.current;
        state.theta = thetaRef.current;
        state.width = width * 2;
        state.height = width * 2;
      },
    });

    return () => {
      globe.destroy();
      window.removeEventListener("resize", onResize);
    };
  }, [markers]);

  return (
    <div className="relative aspect-square w-full max-w-[400px] mx-auto">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ contain: "layout paint size", cursor: "grab" }}
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
        onPointerOut={onPointerOut}
        onPointerMove={onPointerMove}
      />
    </div>
  );
}
