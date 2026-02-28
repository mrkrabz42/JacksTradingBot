"use client";

import { useEffect, useState } from "react";
import { formatInTimeZone } from "date-fns-tz";
import { useTimezone } from "@/lib/context/timezone-context";

export function MarketClock() {
  const { selected } = useTimezone();
  const [time, setTime] = useState("");
  const [date, setDate] = useState("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(formatInTimeZone(now, selected.iana, "HH:mm:ss"));
      setDate(formatInTimeZone(now, selected.iana, "EEEE, dd MMM yyyy"));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [selected.iana]);

  return (
    <div className="text-center py-4">
      <p className="text-3xl font-mono font-bold text-white tracking-wider">{time}</p>
      <p className="text-xs text-muted-foreground mt-1">{date}</p>
      <p className="text-xs text-pink mt-1">{selected.flag} {selected.label} ({selected.abbr})</p>
    </div>
  );
}
