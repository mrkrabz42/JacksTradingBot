"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, RefreshCw, Bell } from "lucide-react";
import { formatInTimeZone } from "date-fns-tz";
import { useTimezone } from "@/lib/context/timezone-context";
import { useSidebar } from "@/lib/context/sidebar-context";
import { NAV_ITEMS } from "@/lib/constants";

export function TopBar() {
  const pathname = usePathname();
  const { selected } = useTimezone();
  const { setMobileOpen } = useSidebar();
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => {
      setTime(formatInTimeZone(new Date(), selected.iana, "HH:mm:ss"));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [selected.iana]);

  const pageTitle = (() => {
    if (pathname === "/") return "Dashboard";
    const item = NAV_ITEMS.find((n) => n.href !== "/" && pathname.startsWith(n.href));
    return item?.label ?? "Dashboard";
  })();

  return (
    <header className="h-14 border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-30 flex items-center px-4 gap-4">
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden text-muted-foreground hover:text-white"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Page title */}
      <h2 className="text-lg font-semibold text-white">{pageTitle}</h2>

      {/* Center: live dot */}
      <div className="hidden sm:flex items-center gap-2 ml-auto mr-auto">
        <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
        <span className="text-xs text-muted-foreground">ANALYZING</span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3 ml-auto">
        <button
          onClick={() => window.location.reload()}
          className="text-muted-foreground hover:text-white transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4" />
        </button>

        <span className="text-sm text-muted-foreground font-mono hidden sm:inline">
          {selected.flag} {time}
        </span>

        <button className="text-muted-foreground hover:text-white transition-colors relative">
          <Bell className="h-4 w-4" />
        </button>

        <div className="h-8 w-8 rounded-full bg-pink/20 flex items-center justify-center text-xs font-bold text-pink">
          MK
        </div>
      </div>
    </header>
  );
}
