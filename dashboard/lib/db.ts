import Database from "better-sqlite3";
import path from "path";
import { MOCK_TRADES } from "./mock-trades";

const DB_PATH = path.join(process.cwd(), "data", "trading.db");

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma("journal_mode = WAL");
    _db.pragma("foreign_keys = ON");
    runMigrations(_db);
  }
  return _db;
}

function runMigrations(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS trade_explanations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trade_id TEXT UNIQUE NOT NULL,
      strategy_name TEXT,
      signal_description TEXT,
      timing_description TEXT,
      risk_description TEXT,
      rules_applied TEXT,
      exit_description TEXT,
      generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS user_feedback (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trade_id TEXT NOT NULL,
      user_name TEXT DEFAULT 'Trader',
      comment TEXT,
      sentiment TEXT CHECK(sentiment IN ('good', 'bad', 'questionable')),
      tags TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS strategy_rules (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rule_name TEXT NOT NULL,
      rule_description TEXT,
      rule_type TEXT CHECK(rule_type IN ('filter', 'entry', 'exit', 'risk')),
      enabled INTEGER DEFAULT 1,
      created_by TEXT DEFAULT 'system',
      backtest_result TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  // Seed default rules if table is empty
  const count = db.prepare("SELECT COUNT(*) as count FROM strategy_rules").get() as { count: number };
  if (count.count === 0) {
    const insert = db.prepare(
      "INSERT INTO strategy_rules (rule_name, rule_description, rule_type, enabled, created_by) VALUES (?, ?, ?, ?, ?)"
    );
    const seeds = [
      ["SMA Crossover (20/50)", "Enter long when 20-period SMA crosses above 50-period SMA. Exit when it crosses below.", "entry", 1, "system"],
      ["NY Session Only", "Only execute trades between 09:30-16:00 ET for maximum liquidity and tighter spreads.", "filter", 1, "system"],
      ["Max 2% Risk Per Trade", "Never risk more than 2% of total portfolio value on a single trade. Position size accordingly.", "risk", 1, "system"],
      ["Max 5 Open Positions", "Limit concurrent open positions to 5 to manage portfolio concentration risk.", "risk", 1, "system"],
      ["Daily Loss Limit 5%", "Stop all trading for the day if cumulative losses reach 5% of portfolio value.", "risk", 1, "system"],
    ];
    for (const [name, desc, type, enabled, by] of seeds) {
      insert.run(name, desc, type, enabled, by);
    }
  }

  // Pre-seed explanations for all mock trades so they load instantly
  seedMockExplanations(db);
}

// Helper: generate a rich, natural explanation for a trade from Alpaca data
export function generateBasicExplanation(
  trade: {
    id: string;
    symbol: string;
    side: string;
    qty: string;
    price: string;
    transaction_time: string;
  },
  tradeIndex?: number
) {
  const price = parseFloat(trade.price);
  const qty = parseInt(trade.qty, 10);
  const total = (qty * price).toFixed(2);
  const stopPrice = (price * 0.98).toFixed(2);
  const targetPrice = (price * 1.04).toFixed(2);
  const idx = tradeIndex ?? 0;

  // --- Session / Timing ---
  const sessionLabel = "New York session (09:30\u201316:00 ET)";

  const buyTimingVariants = [
    `Executed during the ${sessionLabel} when liquidity is deepest and spreads are tightest. The fill came through cleanly with minimal slippage.`,
    `Filled during the ${sessionLabel} \u2014 the most active window for SPY. Bid-ask spread was tight at the time of execution, ensuring a quality entry.`,
    `Order routed during the ${sessionLabel} for optimal fill quality. SPY volume was running above its 20-day average at the time of entry.`,
    `Timed within the ${sessionLabel} to take advantage of peak institutional flow. The entry was placed after the opening volatility settled.`,
    `Execution landed mid-${sessionLabel} when market depth is strongest. SPY\u2019s order book was healthy, and the fill was at the expected price.`,
    `Traded during the ${sessionLabel} as required by the session filter rule. Liquidity conditions were favorable with a sub-penny effective spread.`,
  ];

  const sellTimingVariants = [
    `Closed during the ${sessionLabel} to ensure best execution on the exit. Volume was sufficient for a clean fill without moving the price.`,
    `Exit filled during the ${sessionLabel} when SPY liquidity is at its peak. The position was unwound smoothly at the quoted price.`,
    `Sold within the ${sessionLabel} window. The exit was timed after the midday consolidation period, capturing a stable price level.`,
    `Execution completed during the ${sessionLabel}. The late-session fill benefited from strong closing-auction liquidity.`,
    `Order filled in the ${sessionLabel} as the session filter requires. Market conditions allowed for a tight exit with negligible slippage.`,
    `Exited during the ${sessionLabel} to maximize fill quality. The closing hours provided ample depth to absorb the position.`,
  ];

  // --- Signal ---
  const buySignalVariants = [
    `The 20-day SMA crossed above the 50-day SMA on ${trade.symbol}, confirming a bullish trend shift. Volume picked up on the crossover day, adding confidence to the entry signal.`,
    `Bullish golden cross detected \u2014 the 20-period SMA moved above the 50-period SMA on ${trade.symbol}. The crossover was confirmed by a consecutive higher close, reducing the chance of a false signal.`,
    `${trade.symbol}\u2019s short-term moving average (20-day) crossed above the long-term (50-day), signaling upward momentum. Price had been consolidating just below the 50-SMA before the breakout.`,
    `SMA Crossover triggered on ${trade.symbol} after the 20-day average cleared the 50-day average. The prior three sessions showed building momentum with higher lows leading into the cross.`,
    `Entry signal fired as the 20-day SMA overtook the 50-day SMA on ${trade.symbol}. Daily candle closed firmly above both averages, confirming the trend direction before the order was placed.`,
    `A clean bullish crossover formed on ${trade.symbol} \u2014 the fast SMA (20) crossed above the slow SMA (50). The signal was supported by above-average volume on the crossover candle.`,
  ];

  const sellSignalVariants = [
    `Exit triggered as the 20-day SMA crossed below the 50-day SMA on ${trade.symbol}, indicating momentum reversal. The bearish crossover confirmed the trend change after two days of declining closes.`,
    `The 20-period SMA fell below the 50-period SMA on ${trade.symbol}, generating a sell signal. Price had already started weakening before the official crossover, but the strategy waited for confirmation.`,
    `Bearish death cross on ${trade.symbol} \u2014 the short-term average dropped below the long-term average. The crossover was preceded by a failed bounce off the 50-SMA, adding conviction to the exit.`,
    `Strategy exit triggered on ${trade.symbol} as the 20-day SMA rolled over and crossed below the 50-day SMA. Volume expanded on the down move, confirming distribution pressure.`,
    `Sell signal confirmed when ${trade.symbol}\u2019s fast moving average (20-day) broke below the slow average (50-day). The signal aligned with a break of the prior swing low, reinforcing the exit decision.`,
    `${trade.symbol} flashed a bearish SMA crossover \u2014 the 20-day average crossed under the 50-day average. The trend had been losing steam for several sessions before the signal formally triggered.`,
  ];

  // --- Risk ---
  const buyRiskVariants = [
    `Position sized at ${qty} shares ($${total} total) \u2014 representing roughly 2% of portfolio value. Stop-loss placed 2% below entry at ~$${stopPrice} to cap downside.`,
    `Allocated ${qty} shares at $${price} ($${total} notional), staying within the 2% per-trade risk budget. A hard stop at ~$${stopPrice} limits the maximum loss on this position.`,
    `Risk-managed entry: ${qty} shares purchased for $${total}. The position size was calculated so that a move to the stop at ~$${stopPrice} would represent no more than 2% of total equity.`,
    `Bought ${qty} shares at $${price}/share ($${total} total exposure). Position sizing ensured this trade risks at most 2% of the portfolio. Stop-loss set at ~$${stopPrice}.`,
    `Entered with ${qty} shares ($${total} total) \u2014 sized to keep risk under the 2% portfolio threshold. Protective stop placed at ~$${stopPrice}, which is 2% below the entry price.`,
    `Portfolio risk check passed: ${qty} shares at $${price} = $${total}. This falls within the 2% max risk rule. Downside is capped by a stop-loss order at ~$${stopPrice}.`,
  ];

  const sellRiskVariants = [
    `Closed ${qty} shares at $${price} ($${total} total). Original risk parameters were maintained throughout the holding period \u2014 the stop-loss was never adjusted.`,
    `Exited the full ${qty}-share position at $${price}/share ($${total} proceeds). The 2% risk rule was honored from entry to exit with no manual overrides.`,
    `Sold ${qty} shares for $${total}. Risk management stayed intact throughout the trade \u2014 position size was never increased, and the stop-loss remained in place until the exit signal.`,
    `Position of ${qty} shares closed at $${price} ($${total} total). The trade adhered to all risk limits: 2% max risk, stop-loss active, and no additional scaling into the position.`,
    `Liquidated ${qty} shares at $${price} for $${total}. The original bracket order\u2019s risk parameters were maintained throughout. No discretionary changes were made.`,
    `Full exit: ${qty} shares at $${price} = $${total}. The position was managed within the 2% risk envelope from open to close. All protective orders were kept in place.`,
  ];

  // --- Exit ---
  const buyExitVariants = [
    `Position opened with bracket order. Stop-loss at ~$${stopPrice} and take-profit target at ~$${targetPrice} (2:1 R:R ratio). The bot will manage the exit automatically.`,
    `Bracket order attached: stop-loss at ~$${stopPrice}, take-profit at ~$${targetPrice}, giving a 2:1 reward-to-risk ratio. No manual intervention needed.`,
    `Entry accompanied by automatic exit orders \u2014 stop at ~$${stopPrice} to protect against downside, target at ~$${targetPrice} for a 2:1 R:R. The position is fully managed.`,
    `Stop-loss set at ~$${stopPrice} (2% below entry), take-profit at ~$${targetPrice} (4% above). This gives a clean 2:1 R:R profile on the trade.`,
    `Bracket order in place: downside protection at ~$${stopPrice}, upside target at ~$${targetPrice}. The 2:1 reward-to-risk ratio meets the strategy\u2019s minimum threshold.`,
    `Position is bracketed with a stop at ~$${stopPrice} and a profit target at ~$${targetPrice}. Risk is defined and the exit will trigger automatically on either side.`,
  ];

  const sellExitVariants = [
    `Position closed via strategy exit signal. P&L locked in at the crossover reversal point \u2014 no discretionary hold was applied.`,
    `Exit executed at the SMA crossover reversal. The position was closed mechanically per the strategy rules, locking in the result.`,
    `The strategy\u2019s exit signal fired and the position was closed. The bracket order was canceled and the fill was taken at the market crossover price.`,
    `Closed by the SMA Crossover exit rule. The original bracket orders were replaced by this signal-driven exit, and the P&L was realized.`,
    `Position unwound on the bearish crossover signal. The strategy exited at the reversal point rather than waiting for the stop or target to be hit.`,
    `Strategy-driven exit at the crossover. The trade was closed per the systematic rules \u2014 the bot does not hold through confirmed reversals.`,
  ];

  // --- Rules (always the same 5, as all mock trades use the same strategy) ---
  const rulesApplied = JSON.stringify([
    "SMA Crossover (20/50)",
    "NY Session Only",
    "Max 2% Risk Per Trade",
    "Max 5 Open Positions",
    "Daily Loss Limit 5%",
  ]);

  const isBuy = trade.side === "buy";
  const pick = (arr: string[]) => arr[idx % arr.length];

  return {
    trade_id: trade.id,
    strategy_name: "SMA Crossover (20/50)",
    signal_description: pick(isBuy ? buySignalVariants : sellSignalVariants),
    timing_description: pick(isBuy ? buyTimingVariants : sellTimingVariants),
    risk_description: pick(isBuy ? buyRiskVariants : sellRiskVariants),
    rules_applied: rulesApplied,
    exit_description: pick(isBuy ? buyExitVariants : sellExitVariants),
  };
}

// Pre-seed explanations for all mock trades into the database
function seedMockExplanations(db: Database.Database) {
  const existingCount = db
    .prepare("SELECT COUNT(*) as count FROM trade_explanations")
    .get() as { count: number };

  // Only seed if there are fewer explanations than mock trades (allows re-seeding if new trades added)
  if (existingCount.count >= MOCK_TRADES.length) return;

  const insert = db.prepare(`
    INSERT OR IGNORE INTO trade_explanations
    (trade_id, strategy_name, signal_description, timing_description, risk_description, rules_applied, exit_description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  const seedAll = db.transaction(() => {
    for (let i = 0; i < MOCK_TRADES.length; i++) {
      const trade = MOCK_TRADES[i];
      const explanation = generateBasicExplanation(trade, i);
      insert.run(
        explanation.trade_id,
        explanation.strategy_name,
        explanation.signal_description,
        explanation.timing_description,
        explanation.risk_description,
        explanation.rules_applied,
        explanation.exit_description
      );
    }
  });

  seedAll();
}
