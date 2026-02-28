"use client";

import { useEffect, useRef, useState } from "react";
import { useTradeExplanation, ensureExplanation } from "@/lib/hooks/use-trade-explanations";
import { useUserFeedback, submitFeedback } from "@/lib/hooks/use-user-feedback";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { formatTime } from "@/lib/utils";
import { useTimezone } from "@/lib/context/timezone-context";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  Bot, MessageSquare, Send, ThumbsUp, ThumbsDown, HelpCircle,
  Shield, Clock, BarChart3, Target, CheckCircle2, Tag,
} from "lucide-react";
import type { Trade } from "@/lib/types";

interface TradeDetailProps {
  trade: Trade;
}

const TAGS = [
  { key: "perfect_entry", label: "Perfect Entry", color: "text-success bg-success/10" },
  { key: "too_early", label: "Too Early", color: "text-yellow-500 bg-yellow-500/10" },
  { key: "too_late", label: "Too Late", color: "text-orange-400 bg-orange-400/10" },
  { key: "mss_confirmed", label: "MSS Confirmed", color: "text-cyan bg-cyan/10" },
  { key: "fvg_entry", label: "FVG Entry", color: "text-purple-400 bg-purple-400/10" },
  { key: "stop_too_tight", label: "Stop Too Tight", color: "text-loss bg-loss/10" },
  { key: "good_rr", label: "Good R:R", color: "text-success bg-success/10" },
  { key: "oversize", label: "Oversized", color: "text-loss bg-loss/10" },
] as const;

export function TradeDetail({ trade }: TradeDetailProps) {
  const { selected } = useTimezone();
  const { explanation, isLoading: expLoading } = useTradeExplanation(trade.id);
  const { feedback, isLoading: fbLoading } = useUserFeedback(trade.id);
  const [comment, setComment] = useState("");
  const [sentiment, setSentiment] = useState<string | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Track whether we've already attempted generation for this trade
  const generationAttempted = useRef<string | null>(null);

  // Auto-generate explanation if missing
  useEffect(() => {
    if (expLoading) return; // Still loading, wait
    if (explanation) return; // Already have it
    if (generationAttempted.current === trade.id) return; // Already tried for this trade

    generationAttempted.current = trade.id;
    ensureExplanation(trade);
  }, [expLoading, explanation, trade.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleToggleTag = (key: string) => {
    setSelectedTags((prev) =>
      prev.includes(key) ? prev.filter((t) => t !== key) : [...prev, key]
    );
  };

  const handleSubmitFeedback = async () => {
    if (!comment.trim() && !sentiment && selectedTags.length === 0) return;
    setSubmitting(true);
    try {
      await submitFeedback(trade.id, comment.trim(), sentiment ?? "", selectedTags);
      setComment("");
      setSentiment(null);
      setSelectedTags([]);
      toast.success("Feedback saved", {
        description: `Your review for ${trade.symbol} has been recorded.`,
      });
    } catch {
      toast.error("Failed to save feedback");
    }
    setSubmitting(false);
  };

  const rulesApplied: string[] = explanation?.rules_applied
    ? (() => { try { return JSON.parse(explanation.rules_applied); } catch { return []; } })()
    : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
      {/* Bot Explanation */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-pink" />
          <span className="text-sm font-medium text-pink">Bot Explanation</span>
        </div>

        {expLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : explanation ? (
          <div className="space-y-3 text-sm">
            <div className="bg-background/50 rounded-lg p-3 space-y-2">
              <div className="flex items-start gap-2">
                <BarChart3 className="h-4 w-4 text-cyan mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-muted-foreground font-medium uppercase">Signal</p>
                  <p className="text-white">{explanation.signal_description}</p>
                </div>
              </div>
            </div>

            <div className="bg-background/50 rounded-lg p-3 space-y-2">
              <div className="flex items-start gap-2">
                <Clock className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-muted-foreground font-medium uppercase">Timing</p>
                  <p className="text-white">{explanation.timing_description}</p>
                </div>
              </div>
            </div>

            <div className="bg-background/50 rounded-lg p-3 space-y-2">
              <div className="flex items-start gap-2">
                <Shield className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-muted-foreground font-medium uppercase">Risk</p>
                  <p className="text-white">{explanation.risk_description}</p>
                </div>
              </div>
            </div>

            {rulesApplied.length > 0 && (
              <div className="bg-background/50 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Rules Checked</p>
                    <div className="flex flex-wrap gap-1">
                      {rulesApplied.map((rule: string) => (
                        <span key={rule} className="text-xs bg-success/10 text-success px-2 py-0.5 rounded">
                          {rule}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-background/50 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <Target className="h-4 w-4 text-pink mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-muted-foreground font-medium uppercase">Exit</p>
                  <p className="text-white">{explanation.exit_description}</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-background/50 rounded-lg p-6 flex flex-col items-center gap-2">
            <Bot className="h-6 w-6 text-muted-foreground animate-pulse" />
            <p className="text-sm text-muted-foreground">Generating explanation...</p>
          </div>
        )}
      </div>

      {/* User Feedback */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-cyan" />
          <span className="text-sm font-medium text-cyan">Your Feedback</span>
        </div>

        {/* Existing feedback */}
        {fbLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : feedback.length > 0 ? (
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {feedback.map((fb) => {
              const tags: string[] = fb.tags
                ? (() => { try { return JSON.parse(fb.tags); } catch { return []; } })()
                : [];
              return (
                <div key={fb.id} className="bg-background/50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm">
                      {fb.sentiment === "good" ? "\ud83d\udc4d" : fb.sentiment === "bad" ? "\ud83d\udc4e" : fb.sentiment === "questionable" ? "\ud83e\udd14" : "\u26aa"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(fb.created_at, selected.iana)}
                    </span>
                  </div>
                  {fb.comment && <p className="text-sm text-white">{fb.comment}</p>}
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {tags.map((tag) => {
                        const tagDef = TAGS.find((t) => t.key === tag);
                        return (
                          <span key={tag} className={cn("text-xs px-1.5 py-0.5 rounded", tagDef?.color ?? "text-muted-foreground bg-secondary")}>
                            {tagDef?.label ?? tag}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">No feedback yet. Be the first to review this trade.</p>
        )}

        <Separator className="bg-border" />

        {/* New feedback form */}
        <div className="space-y-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add your observation or question..."
            className="w-full bg-background border border-border rounded-lg p-3 text-sm text-white placeholder:text-muted-foreground resize-none h-20 focus:outline-none focus:ring-1 focus:ring-pink"
          />

          {/* Tag selector */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Tag className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Tags:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {TAGS.map((tag) => (
                <button
                  key={tag.key}
                  onClick={() => handleToggleTag(tag.key)}
                  className={cn(
                    "text-xs px-2 py-0.5 rounded transition-colors border",
                    selectedTags.includes(tag.key)
                      ? `${tag.color} border-current`
                      : "text-muted-foreground bg-transparent border-border hover:border-muted-foreground"
                  )}
                >
                  {tag.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Sentiment:</span>
              {([
                { key: "good", icon: ThumbsUp, label: "\ud83d\udc4d", color: "text-success bg-success/10" },
                { key: "bad", icon: ThumbsDown, label: "\ud83d\udc4e", color: "text-loss bg-loss/10" },
                { key: "questionable", icon: HelpCircle, label: "\ud83e\udd14", color: "text-yellow-500 bg-yellow-500/10" },
              ] as const).map((s) => (
                <button
                  key={s.key}
                  onClick={() => setSentiment(sentiment === s.key ? null : s.key)}
                  className={cn(
                    "text-lg px-2 py-1 rounded transition-colors",
                    sentiment === s.key ? s.color : "opacity-40 hover:opacity-70"
                  )}
                >
                  {s.label}
                </button>
              ))}
            </div>

            <button
              onClick={handleSubmitFeedback}
              disabled={submitting || (!comment.trim() && !sentiment && selectedTags.length === 0)}
              className="flex items-center gap-1.5 bg-pink/10 text-pink px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-pink/20 transition-colors disabled:opacity-40"
            >
              <Send className="h-3 w-3" />
              {submitting ? "Saving..." : "Save"}
            </button>
          </div>
        </div>

        <Separator className="bg-border" />

        {/* Phase 4: Ask the Bot */}
        <div className="opacity-50">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground font-medium">Ask Bonsai (Phase 4)</span>
          </div>
          <div className="flex gap-2">
            <input
              disabled
              placeholder="Why didn't you wait for 2 PM?"
              className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
            />
            <button disabled className="bg-secondary text-muted-foreground px-3 py-2 rounded-lg text-xs cursor-not-allowed">
              Ask
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
