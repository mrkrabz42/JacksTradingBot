"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { LOCALSTORAGE_KEY_SIDEBAR } from "@/lib/constants";

interface SidebarContextValue {
  collapsed: boolean;
  toggleSidebar: () => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

const SidebarContext = createContext<SidebarContextValue | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(LOCALSTORAGE_KEY_SIDEBAR);
    if (stored === "true") setCollapsed(true);
  }, []);

  const toggleSidebar = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(LOCALSTORAGE_KEY_SIDEBAR, String(next));
      return next;
    });
  };

  return (
    <SidebarContext.Provider value={{ collapsed, toggleSidebar, mobileOpen, setMobileOpen }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar(): SidebarContextValue {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider");
  return ctx;
}
