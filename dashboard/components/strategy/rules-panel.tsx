"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useStrategyRules,
  toggleRule,
  addRule,
  deleteRule,
  parseRuleWithAI,
} from "@/lib/hooks/use-strategy-rules";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  Shield, Crosshair, LogOut, Filter, Plus, X, Lock, Sparkles, Loader2,
} from "lucide-react";

const TYPE_META: Record<string, { icon: typeof Shield; color: string; label: string }> = {
  risk: { icon: Shield, color: "text-loss", label: "Risk" },
  entry: { icon: Crosshair, color: "text-success", label: "Entry" },
  exit: { icon: LogOut, color: "text-yellow-500", label: "Exit" },
  filter: { icon: Filter, color: "text-cyan", label: "Filter" },
};

export function RulesPanel() {
  const { rules, isLoading } = useStrategyRules();
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null);

  const handleParseAndAdd = async () => {
    if (!input.trim()) return;
    setAdding(true);
    setParsing(true);
    try {
      const parsed = await parseRuleWithAI(input.trim());
      setParsing(false);
      await addRule(parsed.rule_name, parsed.rule_description, parsed.rule_type);
      setInput("");
      setShowAdd(false);
      toast.success("Rule added", { description: parsed.rule_name });
    } catch {
      toast.error("Failed to add rule");
    }
    setParsing(false);
    setAdding(false);
  };

  const handleToggle = async (id: number, currentEnabled: number) => {
    try {
      await toggleRule(id, !currentEnabled);
    } catch {
      toast.error("Failed to toggle rule");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteRule(id);
      setDeleteConfirm(null);
      toast.success("Rule deleted");
    } catch {
      toast.error("Failed to delete rule");
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">Strategy Rules</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const enabledCount = rules.filter((r) => r.enabled).length;

  return (
    <>
      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
              <Shield className="h-4 w-4 text-pink" />
              Strategy Rules
            </CardTitle>
            <p className="text-xs text-muted-foreground/60 mt-0.5">
              {enabledCount}/{rules.length} active
            </p>
          </div>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-1 text-xs text-pink hover:text-pink-deep transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            Add
          </button>
        </CardHeader>
        <CardContent className="space-y-2">
          {/* Add rule input */}
          {showAdd && (
            <div className="bg-background/50 rounded-lg p-3 space-y-2 border border-border">
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles className="h-3 w-3 text-pink" />
                <span className="text-xs text-muted-foreground">Describe your rule in plain English</span>
              </div>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="e.g. Only trade stocks above their 200 SMA..."
                className="w-full bg-background border border-border rounded-lg p-2.5 text-sm text-white placeholder:text-muted-foreground resize-none h-16 focus:outline-none focus:ring-1 focus:ring-pink"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => { setShowAdd(false); setInput(""); }}
                  className="text-xs text-muted-foreground hover:text-white px-2 py-1 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleParseAndAdd}
                  disabled={adding || !input.trim()}
                  className="flex items-center gap-1.5 bg-pink/10 text-pink px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-pink/20 transition-colors disabled:opacity-40"
                >
                  {parsing ? (
                    <><Loader2 className="h-3 w-3 animate-spin" /> Parsing...</>
                  ) : adding ? (
                    <><Loader2 className="h-3 w-3 animate-spin" /> Adding...</>
                  ) : (
                    <><Sparkles className="h-3 w-3" /> Add Rule</>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Rules list */}
          {rules.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">
              No rules defined. Add your first strategy rule above.
            </p>
          ) : (
            <div className="space-y-1.5">
              {rules.map((rule) => {
                const meta = TYPE_META[rule.rule_type] ?? TYPE_META.filter;
                const Icon = meta.icon;
                return (
                  <div
                    key={rule.id}
                    className={cn(
                      "group relative bg-background/50 rounded-lg p-3 transition-opacity",
                      !rule.enabled && "opacity-50"
                    )}
                  >
                    {/* Delete (X) or Lock icon — on the card border top-right */}
                    {rule.created_by !== "system" ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeleteConfirm({ id: rule.id, name: rule.rule_name }); }}
                        className="absolute -top-2 -right-2 z-10 p-1 rounded-full bg-card border border-border text-muted-foreground hover:text-loss hover:border-loss hover:bg-loss/10 opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    ) : (
                      <div className="absolute -top-2 -right-2 z-10 p-1 rounded-full bg-card border border-border text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                        <Lock className="h-3 w-3" />
                      </div>
                    )}

                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        <Icon className={cn("h-4 w-4 mt-0.5 flex-shrink-0", meta.color)} />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-white truncate">
                              {rule.rule_name}
                            </span>
                            <span className={cn("text-[10px] px-1.5 py-0.5 rounded uppercase font-medium", `${meta.color} bg-current/10`)}>
                              {meta.label}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                            {rule.rule_description}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        {/* Toggle switch */}
                        <button
                          onClick={() => handleToggle(rule.id, rule.enabled)}
                          className={cn(
                            "relative w-8 h-4.5 rounded-full transition-colors",
                            rule.enabled ? "bg-success" : "bg-secondary"
                          )}
                          style={{ width: 32, height: 18 }}
                        >
                          <span
                            className={cn(
                              "absolute top-0.5 w-3.5 h-3.5 rounded-full bg-white transition-transform",
                              rule.enabled ? "left-[15px]" : "left-0.5"
                            )}
                            style={{ width: 14, height: 14 }}
                          />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete confirmation dialog */}
      {deleteConfirm && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
          onClick={() => setDeleteConfirm(null)}
        >
          <div
            className="bg-card border border-border rounded-xl p-5 max-w-sm w-full mx-4 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-white font-semibold">Delete rule?</h3>
            <p className="text-sm text-muted-foreground">
              This will permanently remove &ldquo;{deleteConfirm.name}&rdquo; from your strategy.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="text-sm text-muted-foreground hover:text-white px-3 py-1.5 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm.id)}
                className="text-sm bg-loss/10 text-loss hover:bg-loss/20 px-3 py-1.5 rounded-lg font-medium transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
