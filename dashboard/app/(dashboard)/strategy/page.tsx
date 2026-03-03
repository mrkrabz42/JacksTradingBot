"use client";

import useSWR from "swr";

interface StrategyScore {
  strategy_name: string;
  regime: string;
  win_rate: number;
  avg_pnl_pct: number;
  profit_factor: number;
  avg_r_multiple: number;
  trade_count: number;
  composite_score: number;
  kelly_fraction: number;
  updated_at: string;
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

function scoreColor(score: number): string {
  if (score >= 0.6) return "text-emerald-400";
  if (score >= 0.4) return "text-yellow-400";
  return "text-red-400";
}

function barColor(score: number): string {
  if (score >= 0.6) return "bg-emerald-500";
  if (score >= 0.4) return "bg-yellow-500";
  return "bg-red-500";
}

function effectiveRisk(kellyFraction: number, tradeCount: number): string {
  if (tradeCount < 10) return "2.0%";
  const risk = Math.max(0.5, Math.min(2.0, 2.0 * kellyFraction));
  return risk.toFixed(1) + "%";
}

export default function StrategyPage() {
  const { data, error, isLoading } = useSWR<{ scores: StrategyScore[]; message?: string }>(
    "/api/strategy-scores",
    fetcher,
    { refreshInterval: 30_000 }
  );

  const scores = data?.scores ?? [];
  const overallScores = scores.filter((s) => s.regime === "ALL");
  const hasData = overallScores.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Strategy Scorecard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Live performance metrics &middot; Adaptive Kelly sizing
        </p>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          Failed to load strategy scores: {error.message || "Unknown error"}
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
          Loading strategy scores...
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !hasData && (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <p className="text-muted-foreground">
            {data?.message || "No strategy scores available yet. The bot needs closed trades to compute metrics."}
          </p>
        </div>
      )}

      {/* Live Performance Table */}
      {hasData && (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-white">Live Performance</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground text-left">
                  <th className="px-4 py-3 font-medium">Strategy</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium text-right">Win Rate</th>
                  <th className="px-4 py-3 font-medium text-right">Profit Factor</th>
                  <th className="px-4 py-3 font-medium text-right">Avg R</th>
                  <th className="px-4 py-3 font-medium text-right">Kelly %</th>
                  <th className="px-4 py-3 font-medium text-right">Eff. Risk</th>
                  <th className="px-4 py-3 font-medium text-right">Trades</th>
                </tr>
              </thead>
              <tbody>
                {overallScores.map((s) => (
                  <tr key={s.strategy_name} className="border-b border-border/50 hover:bg-white/[0.02]">
                    {/* Strategy name + learning badge */}
                    <td className="px-4 py-3 font-medium text-white">
                      {s.strategy_name}
                      {s.trade_count < 10 && (
                        <span className="ml-2 text-[10px] font-medium text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded">
                          learning
                        </span>
                      )}
                    </td>

                    {/* Composite score with bar */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-white/10 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${barColor(s.composite_score)}`}
                            style={{ width: `${s.composite_score * 100}%` }}
                          />
                        </div>
                        <span className={`text-xs font-mono ${scoreColor(s.composite_score)}`}>
                          {(s.composite_score * 100).toFixed(0)}
                        </span>
                      </div>
                    </td>

                    {/* Win Rate */}
                    <td className={`px-4 py-3 text-right font-mono ${scoreColor(s.win_rate)}`}>
                      {(s.win_rate * 100).toFixed(1)}%
                    </td>

                    {/* Profit Factor */}
                    <td className={`px-4 py-3 text-right font-mono ${s.profit_factor >= 1.5 ? "text-emerald-400" : s.profit_factor >= 1.0 ? "text-yellow-400" : "text-red-400"}`}>
                      {s.profit_factor.toFixed(2)}
                    </td>

                    {/* Avg R-multiple */}
                    <td className={`px-4 py-3 text-right font-mono ${s.avg_r_multiple >= 1.0 ? "text-emerald-400" : s.avg_r_multiple >= 0 ? "text-yellow-400" : "text-red-400"}`}>
                      {s.avg_r_multiple >= 0 ? "+" : ""}{s.avg_r_multiple.toFixed(2)}R
                    </td>

                    {/* Kelly % */}
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                      {(s.kelly_fraction * 100).toFixed(1)}%
                    </td>

                    {/* Effective Risk */}
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                      {effectiveRisk(s.kelly_fraction, s.trade_count)}
                    </td>

                    {/* Trade Count */}
                    <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                      {s.trade_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Per-Regime Breakdown (only if we have regime-specific data) */}
      {scores.filter((s) => s.regime !== "ALL").length > 0 && (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-white">Per-Regime Breakdown</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground text-left">
                  <th className="px-4 py-3 font-medium">Strategy</th>
                  <th className="px-4 py-3 font-medium">Regime</th>
                  <th className="px-4 py-3 font-medium text-right">Score</th>
                  <th className="px-4 py-3 font-medium text-right">Win Rate</th>
                  <th className="px-4 py-3 font-medium text-right">Profit Factor</th>
                  <th className="px-4 py-3 font-medium text-right">Trades</th>
                </tr>
              </thead>
              <tbody>
                {scores
                  .filter((s) => s.regime !== "ALL")
                  .map((s) => (
                    <tr key={`${s.strategy_name}-${s.regime}`} className="border-b border-border/50 hover:bg-white/[0.02]">
                      <td className="px-4 py-3 font-medium text-white">{s.strategy_name}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                          s.regime === "TREND" ? "bg-emerald-500/10 text-emerald-400" :
                          s.regime === "RANGE" ? "bg-blue-500/10 text-blue-400" :
                          "bg-yellow-500/10 text-yellow-400"
                        }`}>
                          {s.regime}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-right font-mono ${scoreColor(s.composite_score)}`}>
                        {(s.composite_score * 100).toFixed(0)}
                      </td>
                      <td className={`px-4 py-3 text-right font-mono ${scoreColor(s.win_rate)}`}>
                        {(s.win_rate * 100).toFixed(1)}%
                      </td>
                      <td className={`px-4 py-3 text-right font-mono ${s.profit_factor >= 1.0 ? "text-emerald-400" : "text-red-400"}`}>
                        {s.profit_factor.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                        {s.trade_count}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
