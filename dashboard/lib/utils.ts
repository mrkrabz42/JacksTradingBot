import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatInTimeZone } from "date-fns-tz";
import { TIMEZONE } from "./constants";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | string): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(num);
}

export function formatPercent(value: number | string): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  const sign = num >= 0 ? "+" : "";
  return `${sign}${(num * 100).toFixed(2)}%`;
}

export function formatTime(dateStr: string, timezone?: string): string {
  return formatInTimeZone(new Date(dateStr), timezone ?? TIMEZONE, "dd MMM HH:mm");
}

export function formatDate(dateStr: string, timezone?: string): string {
  return formatInTimeZone(new Date(dateStr), timezone ?? TIMEZONE, "dd MMM yyyy");
}
