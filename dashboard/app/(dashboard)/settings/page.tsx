"use client";

import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="h-16 w-16 rounded-2xl bg-pink/10 flex items-center justify-center mb-4">
        <Settings className="h-8 w-8 text-pink" />
      </div>
      <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
      <p className="text-muted-foreground max-w-md">
        Bot configuration, API keys, risk parameters, and preferences. Coming soon.
      </p>
    </div>
  );
}
