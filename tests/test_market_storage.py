"""Tests for bot.storage.market_storage.

Run with:
    pytest tests/test_market_storage.py -v
"""
from __future__ import annotations

import os

import pandas as pd
import pytest

# Use an in-memory SQLite DB so tests leave no files behind
_TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def fresh_engine(monkeypatch):
    """Reset the module-level _engine before every test."""
    import bot.storage.market_storage as ms
    monkeypatch.setattr(ms, "_engine", None)
    yield
    # Clean up the engine after each test
    if ms._engine is not None:
        ms._engine.dispose()
    monkeypatch.setattr(ms, "_engine", None)


def _make_df(symbol: str, timeframe: str, n: int = 3) -> pd.DataFrame:
    """Build a minimal snapshot DataFrame with n rows."""
    from bot.snapshots.market_snapshot import build_snapshot_df

    base_ts = pd.Timestamp("2026-01-15 14:00:00", tz="UTC")
    bars = [
        {
            "timestamp_utc": base_ts + pd.Timedelta(minutes=5 * i),
            "open": 100.0 + i,
            "high": 101.0 + i,
            "low": 99.0 + i,
            "close": 100.5 + i,
            "volume": 1000.0 + i * 100,
        }
        for i in range(n)
    ]
    return build_snapshot_df(symbol, timeframe, bars)


# ── init_storage ──────────────────────────────────────────────────────────────

def test_init_storage_creates_table():
    from bot.storage.market_storage import init_storage
    from sqlalchemy import inspect

    init_storage(_TEST_DB_URL)

    import bot.storage.market_storage as ms
    inspector = inspect(ms._engine)
    assert "market_snapshots" in inspector.get_table_names()


def test_get_engine_raises_before_init():
    from bot.storage.market_storage import _get_engine
    with pytest.raises(RuntimeError, match="init_storage"):
        _get_engine()


# ── write_snapshots / load_snapshots ──────────────────────────────────────────

def test_write_and_load_roundtrip():
    from bot.storage.market_storage import init_storage, write_snapshots, load_snapshots

    init_storage(_TEST_DB_URL)
    df_in = _make_df("SPY", "5m", n=3)

    write_snapshots("SPY", "5m", df_in)

    start = pd.Timestamp("2026-01-15", tz="UTC")
    end   = pd.Timestamp("2026-01-16", tz="UTC")
    df_out = load_snapshots("SPY", "5m", start, end)

    assert len(df_out) == 3
    assert list(df_out["symbol"]) == ["SPY", "SPY", "SPY"]
    assert list(df_out["timeframe"]) == ["5m", "5m", "5m"]

    # Core OHLCV values round-trip correctly
    for col in ("open", "high", "low", "close", "volume"):
        assert pytest.approx(list(df_out[col])) == list(df_in[col])


def test_write_filters_other_symbols():
    from bot.storage.market_storage import init_storage, write_snapshots, load_snapshots

    init_storage(_TEST_DB_URL)

    df_spy = _make_df("SPY", "5m", n=2)
    df_aapl = _make_df("AAPL", "5m", n=2)
    combined = pd.concat([df_spy, df_aapl], ignore_index=True)

    write_snapshots("SPY", "5m", combined)  # should only write SPY rows

    start = pd.Timestamp("2026-01-15", tz="UTC")
    end   = pd.Timestamp("2026-01-16", tz="UTC")
    df_out = load_snapshots("SPY", "5m", start, end)
    assert len(df_out) == 2
    assert all(df_out["symbol"] == "SPY")


def test_write_upsert_no_duplicates():
    """Writing the same data twice must not produce duplicate rows."""
    from bot.storage.market_storage import init_storage, write_snapshots, load_snapshots

    init_storage(_TEST_DB_URL)
    df = _make_df("SPY", "5m", n=3)

    write_snapshots("SPY", "5m", df)
    write_snapshots("SPY", "5m", df)  # second write — should upsert, not duplicate

    start = pd.Timestamp("2026-01-15", tz="UTC")
    end   = pd.Timestamp("2026-01-16", tz="UTC")
    df_out = load_snapshots("SPY", "5m", start, end)
    assert len(df_out) == 3


def test_load_respects_time_bounds():
    from bot.storage.market_storage import init_storage, write_snapshots, load_snapshots

    init_storage(_TEST_DB_URL)
    df = _make_df("SPY", "5m", n=5)   # bars at 14:00, 14:05, 14:10, 14:15, 14:20
    write_snapshots("SPY", "5m", df)

    # Load only bars between 14:05 and 14:15 (inclusive) → expect 3 rows
    start = pd.Timestamp("2026-01-15 14:05:00", tz="UTC")
    end   = pd.Timestamp("2026-01-15 14:15:00", tz="UTC")
    df_out = load_snapshots("SPY", "5m", start, end)
    assert len(df_out) == 3


def test_load_empty_when_no_data():
    from bot.storage.market_storage import init_storage, load_snapshots

    init_storage(_TEST_DB_URL)
    df_out = load_snapshots(
        "MISSING", "5m",
        pd.Timestamp("2026-01-01", tz="UTC"),
        pd.Timestamp("2026-01-02", tz="UTC"),
    )
    assert df_out.empty


# ── CSV / Parquet export ──────────────────────────────────────────────────────

def test_export_to_csv(tmp_path):
    from bot.storage.market_storage import init_storage, write_snapshots, export_snapshots_to_csv

    init_storage(_TEST_DB_URL)
    df = _make_df("SPY", "5m", n=3)
    write_snapshots("SPY", "5m", df)

    csv_path = str(tmp_path / "spy_5m.csv")
    export_snapshots_to_csv("SPY", "5m", csv_path)

    df_loaded = pd.read_csv(csv_path)
    assert len(df_loaded) == 3
    assert "open" in df_loaded.columns
    assert "confluence_score" in df_loaded.columns


def test_export_to_parquet(tmp_path):
    from bot.storage.market_storage import init_storage, write_snapshots, export_snapshots_to_parquet

    init_storage(_TEST_DB_URL)
    df = _make_df("SPY", "5m", n=3)
    write_snapshots("SPY", "5m", df)

    pq_path = str(tmp_path / "spy_5m.parquet")
    export_snapshots_to_parquet("SPY", "5m", pq_path)

    df_loaded = pd.read_parquet(pq_path)
    assert len(df_loaded) == 3
    assert "setup_grade" in df_loaded.columns


def test_export_with_date_filter(tmp_path):
    """Export with start/end only returns the filtered slice."""
    from bot.storage.market_storage import (
        init_storage, write_snapshots, export_snapshots_to_csv
    )

    init_storage(_TEST_DB_URL)
    df = _make_df("SPY", "5m", n=5)
    write_snapshots("SPY", "5m", df)

    csv_path = str(tmp_path / "filtered.csv")
    export_snapshots_to_csv(
        "SPY", "5m", csv_path,
        start=pd.Timestamp("2026-01-15 14:05:00", tz="UTC"),
        end=pd.Timestamp("2026-01-15 14:10:00", tz="UTC"),
    )

    df_loaded = pd.read_csv(csv_path)
    assert len(df_loaded) == 2
