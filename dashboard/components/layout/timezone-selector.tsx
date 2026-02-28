"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { useTimezone } from "@/lib/context/timezone-context";
import { TIMEZONE_OPTIONS } from "@/lib/constants";

export function TimezoneSelector() {
  const { selected, setTimezone } = useTimezone();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-white transition-colors px-2 py-1 rounded-md hover:bg-secondary"
      >
        <span>{selected.flag}</span>
        <span>{selected.label}</span>
        <ChevronDown className="h-3 w-3" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-52 bg-elevated border border-border rounded-lg shadow-lg z-50 py-1">
          {TIMEZONE_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => {
                setTimezone(opt.key);
                setOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm transition-colors ${
                opt.key === selected.key
                  ? "text-pink bg-pink/10"
                  : "text-muted-foreground hover:text-white hover:bg-secondary"
              }`}
            >
              <span>{opt.flag}</span>
              <span className="flex-1 text-left">{opt.label}</span>
              <span className="text-xs opacity-60">{opt.abbr}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
