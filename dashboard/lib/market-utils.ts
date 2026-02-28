import { formatInTimeZone } from "date-fns-tz";
import { MARKET_HOURS } from "./constants";
import type { TimezoneKey, MarketStatusResult } from "./types";

function timeToMinutes(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

function formatCountdown(diffMinutes: number): string {
  if (diffMinutes < 0) diffMinutes += 7 * 24 * 60; // wrap around week
  const hours = Math.floor(diffMinutes / 60);
  const mins = diffMinutes % 60;
  if (hours > 24) {
    const days = Math.floor(hours / 24);
    const remHours = hours % 24;
    return `${days}d ${remHours}h`;
  }
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

export function getMarketStatus(now: Date, exchangeKey: TimezoneKey): MarketStatusResult {
  const config = MARKET_HOURS[exchangeKey];
  const dayStr = formatInTimeZone(now, config.timezone, "EEEE");
  const dayMap: Record<string, number> = {
    Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3,
    Thursday: 4, Friday: 5, Saturday: 6,
  };
  const dow = dayMap[dayStr] ?? 0;
  const currentHHMM = formatInTimeZone(now, config.timezone, "HH:mm");
  const currentMin = timeToMinutes(currentHHMM);

  // Weekend check
  if (config.weekends.includes(dow)) {
    // Calculate minutes until Monday open
    const daysUntilMon = dow === 6 ? 2 : 1; // Sat→2, Sun→1
    const firstOpen = timeToMinutes(config.sessions[0].open);
    const minsUntil = daysUntilMon * 24 * 60 + (firstOpen - currentMin);
    return {
      status: "closed",
      label: "Closed (Weekend)",
      countdown: formatCountdown(minsUntil),
      dotColor: "bg-[#666]",
    };
  }

  // Check main sessions
  for (const session of config.sessions) {
    const openMin = timeToMinutes(session.open);
    const closeMin = timeToMinutes(session.close);
    if (currentMin >= openMin && currentMin < closeMin) {
      return {
        status: "open",
        label: "Market Open",
        countdown: formatCountdown(closeMin - currentMin),
        dotColor: "bg-pink",
      };
    }
  }

  // Check extended hours (US only)
  if (config.extendedHours) {
    const pre = config.extendedHours.preMarket;
    const after = config.extendedHours.afterHours;
    const preOpen = timeToMinutes(pre.open);
    const preClose = timeToMinutes(pre.close);
    const afterOpen = timeToMinutes(after.open);
    const afterClose = timeToMinutes(after.close);

    if (currentMin >= preOpen && currentMin < preClose) {
      return {
        status: "pre_market",
        label: "Pre-Market",
        countdown: formatCountdown(preClose - currentMin),
        dotColor: "bg-[#FFA500]",
      };
    }
    if (currentMin >= afterOpen && currentMin < afterClose) {
      return {
        status: "after_hours",
        label: "After Hours",
        countdown: formatCountdown(afterClose - currentMin),
        dotColor: "bg-[#FFA500]",
      };
    }
  }

  // Closed — find next session open
  const firstSessionOpen = timeToMinutes(config.sessions[0].open);
  if (currentMin < firstSessionOpen) {
    // Before today's open
    return {
      status: "closed",
      label: "Closed",
      countdown: formatCountdown(firstSessionOpen - currentMin),
      dotColor: "bg-[#666]",
    };
  }

  // After today's close — next open is tomorrow (or Monday if Friday)
  const daysUntilNext = dow === 5 ? 3 : 1; // Friday→Monday=3 days, else tomorrow
  const minsUntil = daysUntilNext * 24 * 60 + (firstSessionOpen - currentMin);
  return {
    status: "closed",
    label: "Closed",
    countdown: formatCountdown(minsUntil),
    dotColor: "bg-[#666]",
  };
}
