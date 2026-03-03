"""Trade journal — persists trade entries/exits and supports per-strategy queries.

Uses a standalone SQLite database (trade_journal.sqlite) separate from the
market snapshot store.  The journal tracks:
  - Entry records (symbol, strategy, direction, prices, regime)
  - Exit records (fill price, P&L, R-multiple)
  - Closed-trade queries grouped by strategy for the feedback scorecard
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from loguru import logger


_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "trade_journal.sqlite")

_CREATE_TRADES_SQL = """
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    strategy        TEXT NOT NULL,
    direction       TEXT NOT NULL DEFAULT 'BUY',
    entry_price     REAL NOT NULL,
    stop_loss_price REAL,
    target_price    REAL,
    shares          INTEGER NOT NULL DEFAULT 0,
    entry_time      TEXT NOT NULL,
    exit_price      REAL,
    exit_time       TEXT,
    pnl             REAL,
    pnl_pct         REAL,
    r_multiple      REAL,
    status          TEXT NOT NULL DEFAULT 'OPEN',
    regime          TEXT,
    notes           TEXT
);
"""

_CREATE_STRATEGY_SCORES_SQL = """
CREATE TABLE IF NOT EXISTS strategy_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name   TEXT NOT NULL,
    regime          TEXT NOT NULL DEFAULT 'ALL',
    win_rate        REAL DEFAULT 0.0,
    avg_pnl_pct     REAL DEFAULT 0.0,
    profit_factor   REAL DEFAULT 1.0,
    avg_r_multiple  REAL DEFAULT 0.0,
    trade_count     INTEGER DEFAULT 0,
    composite_score REAL DEFAULT 0.5,
    kelly_fraction  REAL DEFAULT 0.0,
    updated_at      TEXT NOT NULL,
    UNIQUE(strategy_name, regime)
);
"""


class TradeJournal:
    """SQLite-backed trade journal with per-strategy query support."""

    def __init__(self, db_path: str | None = None):
        self._db_path = os.path.abspath(db_path or _DB_PATH)
        self._conn: sqlite3.Connection | None = None
        self._connect()

    def _connect(self) -> None:
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")

        # Create tables
        self._conn.execute(_CREATE_TRADES_SQL)
        self._conn.execute(_CREATE_STRATEGY_SCORES_SQL)
        self._conn.commit()

        # Migrate: add regime column if missing (safe no-op on fresh DB)
        try:
            self._conn.execute("ALTER TABLE trades ADD COLUMN regime TEXT")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

        logger.info(f"Trade journal initialized — {self._db_path}")

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._connect()
        return self._conn

    # ── Record entry ─────────────────────────────────────────────────────────

    def record_entry(
        self,
        symbol: str,
        strategy: str,
        direction: str,
        entry_price: float,
        shares: int,
        stop_loss_price: float | None = None,
        target_price: float | None = None,
        regime: str | None = None,
        notes: str | None = None,
    ) -> int:
        """Record a new trade entry. Returns the trade ID."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.execute(
            """INSERT INTO trades
               (symbol, strategy, direction, entry_price, shares,
                stop_loss_price, target_price, entry_time, status, regime, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)""",
            (symbol, strategy, direction, entry_price, shares,
             stop_loss_price, target_price, now, regime, notes),
        )
        self.conn.commit()
        trade_id = cursor.lastrowid
        logger.info(
            f"Journal: ENTRY #{trade_id} {direction} {symbol} x{shares} @ ${entry_price:.2f} "
            f"[{strategy}] regime={regime}"
        )
        return trade_id

    # ── Record exit ──────────────────────────────────────────────────────────

    def record_exit(
        self,
        trade_id: int,
        exit_price: float,
        notes: str | None = None,
    ) -> None:
        """Record trade exit, calculate P&L and R-multiple."""
        row = self.conn.execute(
            "SELECT * FROM trades WHERE id = ?", (trade_id,)
        ).fetchone()
        if row is None:
            logger.error(f"Journal: trade #{trade_id} not found")
            return

        entry_price = row["entry_price"]
        shares = row["shares"]
        direction = row["direction"]
        stop_loss_price = row["stop_loss_price"]

        # Calculate P&L
        if direction == "BUY":
            pnl = (exit_price - entry_price) * shares
            pnl_pct = (exit_price - entry_price) / entry_price if entry_price else 0.0
        else:
            pnl = (entry_price - exit_price) * shares
            pnl_pct = (entry_price - exit_price) / entry_price if entry_price else 0.0

        # R-multiple: how many R did we capture (R = entry - stop)
        r_multiple = 0.0
        if stop_loss_price and stop_loss_price != entry_price:
            risk_per_share = abs(entry_price - stop_loss_price)
            if direction == "BUY":
                r_multiple = (exit_price - entry_price) / risk_per_share
            else:
                r_multiple = (entry_price - exit_price) / risk_per_share

        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """UPDATE trades
               SET exit_price = ?, exit_time = ?, pnl = ?, pnl_pct = ?,
                   r_multiple = ?, status = 'CLOSED', notes = COALESCE(?, notes)
               WHERE id = ?""",
            (exit_price, now, pnl, pnl_pct, r_multiple, notes, trade_id),
        )
        self.conn.commit()
        logger.info(
            f"Journal: EXIT #{trade_id} @ ${exit_price:.2f} | "
            f"P&L: ${pnl:.2f} ({pnl_pct:+.2%}) | R: {r_multiple:+.2f}"
        )

    # ── Strategy queries ─────────────────────────────────────────────────────

    def get_closed_trades_for_strategy(
        self,
        strategy_name: str,
        limit: int = 50,
        regime: str | None = None,
    ) -> list[dict]:
        """Fetch last N closed trades for a strategy, optionally filtered by regime."""
        if regime and regime != "ALL":
            rows = self.conn.execute(
                """SELECT * FROM trades
                   WHERE strategy = ? AND status = 'CLOSED' AND regime = ?
                   ORDER BY exit_time DESC LIMIT ?""",
                (strategy_name, regime, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """SELECT * FROM trades
                   WHERE strategy = ? AND status = 'CLOSED'
                   ORDER BY exit_time DESC LIMIT ?""",
                (strategy_name, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_strategy_names(self) -> list[str]:
        """Return distinct strategy names from closed trades."""
        rows = self.conn.execute(
            "SELECT DISTINCT strategy FROM trades WHERE status = 'CLOSED'"
        ).fetchall()
        return [r["strategy"] for r in rows]

    def get_open_trades(self) -> list[dict]:
        """Return all currently open trades."""
        rows = self.conn.execute(
            "SELECT * FROM trades WHERE status = 'OPEN' ORDER BY entry_time DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
