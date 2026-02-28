"use client";

import { SidebarProvider } from "@/lib/context/sidebar-context";
import { Sidebar } from "@/components/layout/sidebar";
import { TopBar } from "@/components/layout/top-bar";
import { RightPanel } from "@/components/layout/right-panel";
import { ChatButton } from "@/components/shared/chat-button";
import { MSSAlertProvider } from "@/lib/hooks/use-mss-alerts";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar />
          <div className="flex flex-1">
            <main className="flex-1 p-6 overflow-auto">
              {children}
            </main>
            <RightPanel />
          </div>
        </div>
      </div>
      <ChatButton />
      <MSSAlertProvider />
    </SidebarProvider>
  );
}
