const TRADING_BASE = "https://paper-api.alpaca.markets/v2";
const DATA_BASE = "https://data.alpaca.markets/v2";

function getHeaders(): Record<string, string> {
  const key = process.env.ALPACA_API_KEY;
  const secret = process.env.ALPACA_SECRET_KEY;

  if (!key || !secret) {
    throw new Error("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY env vars");
  }

  return {
    "APCA-API-KEY-ID": key,
    "APCA-API-SECRET-KEY": secret,
    "Content-Type": "application/json",
  };
}

export async function fetchTrading(path: string, signal?: AbortSignal): Promise<Response> {
  return fetch(`${TRADING_BASE}${path}`, {
    headers: getHeaders(),
    cache: "no-store",
    signal,
  });
}

export async function fetchData(path: string): Promise<Response> {
  return fetch(`${DATA_BASE}${path}`, {
    headers: getHeaders(),
    cache: "no-store",
  });
}
