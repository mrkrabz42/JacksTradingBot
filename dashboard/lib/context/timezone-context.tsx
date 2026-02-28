"use client";

import { createContext, useContext, useState, useEffect } from "react";
import type { TimezoneKey, TimezoneOption } from "@/lib/types";
import { TIMEZONE_OPTIONS, LOCALSTORAGE_KEY_TZ } from "@/lib/constants";

interface TimezoneContextValue {
  selected: TimezoneOption;
  setTimezone: (key: TimezoneKey) => void;
}

const TimezoneContext = createContext<TimezoneContextValue | null>(null);

const VALID_KEYS = new Set<string>(TIMEZONE_OPTIONS.map((o) => o.key));

function findOption(key: TimezoneKey): TimezoneOption {
  return TIMEZONE_OPTIONS.find((o) => o.key === key) ?? TIMEZONE_OPTIONS[0];
}

export function TimezoneProvider({ children }: { children: React.ReactNode }) {
  const [selected, setSelected] = useState<TimezoneOption>(TIMEZONE_OPTIONS[0]); // default London

  useEffect(() => {
    const stored = localStorage.getItem(LOCALSTORAGE_KEY_TZ);
    if (stored && VALID_KEYS.has(stored)) {
      setSelected(findOption(stored as TimezoneKey));
    }
  }, []);

  const setTimezone = (key: TimezoneKey) => {
    setSelected(findOption(key));
    localStorage.setItem(LOCALSTORAGE_KEY_TZ, key);
  };

  return (
    <TimezoneContext.Provider value={{ selected, setTimezone }}>
      {children}
    </TimezoneContext.Provider>
  );
}

export function useTimezone(): TimezoneContextValue {
  const ctx = useContext(TimezoneContext);
  if (!ctx) throw new Error("useTimezone must be used within TimezoneProvider");
  return ctx;
}
