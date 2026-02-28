"""MarketSnapshot storage layer.

Persists and reloads ``MarketSnapshot`` data via SQLAlchemy (SQLite or Postgres).
This is the **only** module that knows about the database schema.

Usage
-----
    from bot.storage.market_storage import init_storage, write_snapshots, load_snapshots

    init_storage("sqlite:///bot_snapshots.sqlite")
    write_snapshots("SPY", "5m", df)
    df_back = load_snapshots("SPY", "5m", start=pd.Timestamp("2026-01-01", tz="UTC"),
                                          end=pd.Timestamp("2026-02-01", tz="UTC"))
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from bot.snapshots.market_snapshot import MarketSnapshot


# ── Module-level engine singleton ─────────────────────────────────────────────

_engine: Optional[Engine] = None

# Ordered list of all DB columns (mirrors MarketSnapshot field order)
_ALL_COLUMNS: list[str] = list(MarketSnapshot.__dataclass_fields__.keys())

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS market_snapshots (
    symbol                   TEXT      NOT NULL,
    timeframe                TEXT      NOT NULL,
    timestamp_utc            TIMESTAMP NOT NULL,

    open                     REAL      NOT NULL,
    high                     REAL      NOT NULL,
    low                      REAL      NOT NULL,
    close                    REAL      NOT NULL,
    volume                   REAL      NOT NULL,

    session                  TEXT,
    session_high             REAL,
    session_low              REAL,
    session_high_asia        REAL,
    session_low_asia         REAL,
    session_high_london      REAL,
    session_low_london       REAL,
    session_high_ny          REAL,
    session_low_ny           REAL,
    regime                   TEXT,
    volatility_state         TEXT,
    trend_direction          TEXT,
    trend_strength_score     REAL,
    vwap                     REAL,
    poc                      REAL,
    vah                      REAL,
    val                      REAL,
    volume_state             TEXT,
    liquidity_draw_direction TEXT,
    liquidity_magnet_score   REAL,
    htf_bias                 TEXT,
    mtf_structure_bias       TEXT,
    ltf_direction            TEXT,
    mtf_alignment_state      TEXT,
    mtf_alignment_score      REAL,
    breakout_quality_score   REAL,
    breakout_type            TEXT,
    confluence_score         REAL,
    setup_grade              TEXT,
    bar_trade_bias           TEXT,

    rvol_ratio               REAL,
    participation_state      TEXT,
    volume_spike_flag        INTEGER,

    PRIMARY KEY (symbol, timeframe, timestamp_utc)
);
"""


# ── Public API ────────────────────────────────────────────────────────────────

def _migrate_schema(engine: Engine) -> None:
    """Add new columns to an existing table (no-op if they already exist)."""
    new_cols = [
        ("rvol_ratio", "REAL"),
        ("participation_state", "TEXT"),
        ("volume_spike_flag", "INTEGER"),
        ("session_high", "REAL"), ("session_low", "REAL"),
        ("session_high_asia", "REAL"), ("session_low_asia", "REAL"),
        ("session_high_london", "REAL"), ("session_low_london", "REAL"),
        ("session_high_ny", "REAL"), ("session_low_ny", "REAL"),
    ]
    with engine.begin() as conn:
        for name, typ in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE market_snapshots ADD COLUMN {name} {typ}"))
            except Exception:
                pass  # column already exists — safe to ignore


def init_storage(db_url: str) -> None:
    """Initialize the DB engine and ensure the ``market_snapshots`` table exists.

    Parameters
    ----------
    db_url:
        SQLAlchemy connection URL.
        E.g. ``'sqlite:///bot_snapshots.sqlite'`` or a Postgres DSN.
    """
    global _engine
    _engine = create_engine(db_url, future=True)
    with _engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE_SQL))
    _migrate_schema(_engine)
    logger.info(f"Storage initialized — db_url={db_url}")


def write_snapshots(
    symbol: str,
    timeframe: str,
    df_snapshots: pd.DataFrame,
) -> None:
    """Persist a batch of MarketSnapshot rows for a given symbol + timeframe.

    Uses a **delete-then-insert** strategy within a single transaction so
    re-runs never produce duplicate primary keys.

    Parameters
    ----------
    symbol:
        Ticker symbol to persist (e.g. ``"SPY"``).
    timeframe:
        Bar timeframe string (e.g. ``"5m"`` or ``"1h"``).
    df_snapshots:
        DataFrame following the canonical ``MarketSnapshot`` schema.
        Rows for other symbol/timeframe pairs are silently ignored.
    """
    engine = _get_engine()

    # ── Filter to requested symbol + timeframe ────────────────────────────────
    df = df_snapshots.copy()
    if "symbol" in df.columns:
        df = df[df["symbol"] == symbol]
    if "timeframe" in df.columns:
        df = df[df["timeframe"] == timeframe]

    if df.empty:
        logger.debug(f"write_snapshots: no rows for {symbol}/{timeframe} — skipping")
        return

    # ── Keep only schema columns (drop any extras the caller added) ───────────
    cols_present = [c for c in _ALL_COLUMNS if c in df.columns]
    df = df[cols_present].copy()

    # ── Normalize timestamp_utc → naive UTC string (SQLite-safe) ─────────────
    df["timestamp_utc"] = (
        pd.to_datetime(df["timestamp_utc"], utc=True)
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )

    ts_min = df["timestamp_utc"].min()
    ts_max = df["timestamp_utc"].max()

    # ── Delete overlapping range, then insert ─────────────────────────────────
    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM market_snapshots "
                "WHERE symbol = :symbol "
                "  AND timeframe = :timeframe "
                "  AND timestamp_utc BETWEEN :ts_min AND :ts_max"
            ),
            {"symbol": symbol, "timeframe": timeframe, "ts_min": ts_min, "ts_max": ts_max},
        )
        df.to_sql(
            "market_snapshots",
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
        )

    logger.info(
        f"write_snapshots: {len(df)} rows written — "
        f"symbol={symbol} timeframe={timeframe} "
        f"range=[{ts_min} → {ts_max}]"
    )


def load_snapshots(
    symbol: str,
    timeframe: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Load snapshots for a given symbol + timeframe between [start, end].

    Parameters
    ----------
    symbol:
        Ticker symbol.
    timeframe:
        Bar timeframe string.
    start:
        Inclusive lower bound (UTC).
    end:
        Inclusive upper bound (UTC).

    Returns
    -------
    ``pd.DataFrame`` aligned with the canonical ``MarketSnapshot`` schema,
    sorted by ``timestamp_utc`` ascending.  Returns an empty DataFrame if no
    rows match.
    """
    engine = _get_engine()

    ts_start = _ts_to_str(start)
    ts_end = _ts_to_str(end)

    query = text(
        "SELECT * FROM market_snapshots "
        "WHERE symbol    = :symbol "
        "  AND timeframe = :timeframe "
        "  AND timestamp_utc BETWEEN :start AND :end "
        "ORDER BY timestamp_utc ASC"
    )

    with engine.connect() as conn:
        df = pd.read_sql(
            query,
            con=conn,
            params={"symbol": symbol, "timeframe": timeframe, "start": ts_start, "end": ts_end},
        )

    if df.empty:
        logger.debug(
            f"load_snapshots: no rows found for {symbol}/{timeframe} "
            f"[{ts_start} → {ts_end}]"
        )
        return df

    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df.sort_values("timestamp_utc").reset_index(drop=True)

    logger.info(
        f"load_snapshots: {len(df)} rows loaded — "
        f"symbol={symbol} timeframe={timeframe} "
        f"range=[{ts_start} → {ts_end}]"
    )
    return df


def export_snapshots_to_csv(
    symbol: str,
    timeframe: str,
    path: str,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> None:
    """Export snapshots to a CSV file.

    Parameters
    ----------
    symbol:
        Ticker symbol.
    timeframe:
        Bar timeframe string.
    path:
        Destination file path (e.g. ``"exports/SPY_5m.csv"``).
    start:
        Optional lower bound filter (UTC).  Defaults to epoch start.
    end:
        Optional upper bound filter (UTC).  Defaults to far future.
    """
    df = _load_for_export(symbol, timeframe, start, end)
    df.to_csv(path, index=False)
    logger.info(f"export_snapshots_to_csv: {len(df)} rows → {path}")


def export_snapshots_to_parquet(
    symbol: str,
    timeframe: str,
    path: str,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> None:
    """Export snapshots to a Parquet file.

    Parameters
    ----------
    symbol:
        Ticker symbol.
    timeframe:
        Bar timeframe string.
    path:
        Destination file path (e.g. ``"exports/SPY_5m.parquet"``).
    start:
        Optional lower bound filter (UTC).  Defaults to epoch start.
    end:
        Optional upper bound filter (UTC).  Defaults to far future.
    """
    df = _load_for_export(symbol, timeframe, start, end)
    df.to_parquet(path, index=False)
    logger.info(f"export_snapshots_to_parquet: {len(df)} rows → {path}")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError(
            "Storage not initialized. Call init_storage(db_url) first."
        )
    return _engine


def _ts_to_str(ts: pd.Timestamp) -> str:
    """Normalize a Timestamp to a naive UTC string for DB comparison."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _load_for_export(
    symbol: str,
    timeframe: str,
    start: Optional[pd.Timestamp],
    end: Optional[pd.Timestamp],
) -> pd.DataFrame:
    """Resolve optional start/end defaults and delegate to load_snapshots."""
    resolved_start = start if start is not None else pd.Timestamp("1970-01-01", tz="UTC")
    resolved_end = end if end is not None else pd.Timestamp("2099-12-31", tz="UTC")
    return load_snapshots(symbol, timeframe, resolved_start, resolved_end)
