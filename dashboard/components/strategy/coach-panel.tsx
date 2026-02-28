"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Bot, GraduationCap, Lock, Lightbulb, BookOpen, Target,
  TrendingUp, Brain, Zap,
} from "lucide-react";

const TIPS = [
  {
    icon: Target,
    text: "Review every trade within 24 hours for maximum learning retention.",
    color: "text-pink",
  },
  {
    icon: TrendingUp,
    text: "Track your sentiment over time — consistent 'questionable' ratings reveal blind spots.",
    color: "text-success",
  },
  {
    icon: Lightbulb,
    text: "Tag trades to build pattern recognition. Use FVG Entry and MSS Confirmed for ICT concepts.",
    color: "text-yellow-500",
  },
];

const LOCKED_FEATURES = [
  { icon: Brain, label: "AI Trade Review", desc: "Get personalized analysis of each trade" },
  { icon: BookOpen, label: "Learning Paths", desc: "Structured courses based on your mistakes" },
  { icon: Zap, label: "Real-time Alerts", desc: "Get coached during live trading sessions" },
];

const JOURNAL_PROMPTS = [
  "What was your emotional state before this trade?",
  "Did you follow your entry rules exactly?",
  "What would you do differently next time?",
  "Rate your patience on this trade (1-10).",
];

export function CoachPanel() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-pink" />
          Bonsai Coach
          <span className="text-[10px] bg-pink/10 text-pink px-1.5 py-0.5 rounded font-normal">
            Preview
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Trading Tips */}
        <div>
          <p className="text-xs text-muted-foreground font-medium mb-2 uppercase">Quick Tips</p>
          <div className="space-y-2">
            {TIPS.map((tip, i) => {
              const Icon = tip.icon;
              return (
                <div key={i} className="flex items-start gap-2 bg-background/50 rounded-lg p-2.5">
                  <Icon className={cn("h-3.5 w-3.5 mt-0.5 flex-shrink-0", tip.color)} />
                  <p className="text-xs text-muted-foreground leading-relaxed">{tip.text}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Journal Prompts */}
        <div>
          <p className="text-xs text-muted-foreground font-medium mb-2 uppercase">Journal Prompts</p>
          <div className="space-y-1.5">
            {JOURNAL_PROMPTS.map((prompt, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[10px] text-pink font-mono mt-0.5">{i + 1}.</span>
                <p className="text-xs text-muted-foreground italic">{prompt}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Locked Features */}
        <div>
          <p className="text-xs text-muted-foreground font-medium mb-2 uppercase">Coming Soon</p>
          <div className="space-y-1.5">
            {LOCKED_FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <div
                  key={feat.label}
                  className="flex items-center gap-2.5 bg-background/50 rounded-lg p-2.5 opacity-50"
                >
                  <div className="relative flex-shrink-0">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <Lock className="h-2.5 w-2.5 text-muted-foreground absolute -bottom-0.5 -right-0.5" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">{feat.label}</p>
                    <p className="text-[10px] text-muted-foreground/60">{feat.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Ask Bonsai placeholder */}
        <div className="border border-dashed border-border rounded-lg p-3 opacity-60">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="h-4 w-4 text-pink" />
            <span className="text-xs font-medium text-muted-foreground">Ask Bonsai</span>
            <Lock className="h-3 w-3 text-muted-foreground ml-auto" />
          </div>
          <p className="text-[10px] text-muted-foreground mb-2">
            AI-powered coaching that learns from your trading patterns and feedback.
          </p>
          <div className="flex gap-2">
            <input
              disabled
              placeholder="Why do I keep entering too early?"
              className="flex-1 bg-background border border-border rounded px-2 py-1.5 text-xs text-muted-foreground cursor-not-allowed"
            />
            <button disabled className="bg-secondary text-muted-foreground px-2 py-1.5 rounded text-xs cursor-not-allowed">
              Ask
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
