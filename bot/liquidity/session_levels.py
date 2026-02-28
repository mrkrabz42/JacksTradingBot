"""Session High/Low computation module.

Computes true per-session (Asia/London/NY) extremes for each trading day,
adding ``session_high``, ``session_low``, and per-session extreme columns
to a DataFrame.

Usage
-----
    from bot.liquidity.session_levels import add_session_high_low

    df = add_session_high_low(df)   # df must have timestamp_utc, high, low, session

The result uses the **full session aggregate** (all bars in that session for
that day) as the session high/low — the standard trading definition.
``OUTSIDE`` bars receive NaN for ``session_high`` / ``session_low``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# Session label constants (must match bot.sessions.classifier output)
_KNOWN_SESSIONS = ("ASIA", "LONDON", "NY")


def add_session_high_low(df: pd.DataFrame) -> pd.DataFrame:
    """Add session-specific high/low columns to *df*.

    Computes the full session aggregate (all bars in that session for that
    trading day), which is the standard definition for session H/L levels.

    Parameters
    ----------
    df:
        Must contain: ``timestamp_utc``, ``high``, ``low``, ``session``.
        ``session`` values should be ``'ASIA'``, ``'LONDON'``, ``'NY'``,
        or ``'OUTSIDE'``.

    Returns
    -------
    DataFrame with 8 new columns added:
        ``session_high``, ``session_low``,
        ``session_high_asia``, ``session_low_asia``,
        ``session_high_london``, ``session_low_london``,
        ``session_high_ny``, ``session_low_ny``.

    ``OUTSIDE`` bars get ``NaN`` for ``session_high`` / ``session_low``.

    Raises
    ------
    ValueError
        If any of the required columns are absent.
    """
    required = {"timestamp_utc", "high", "low", "session"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"add_session_high_low: missing required columns: {sorted(missing)}"
        )

    out = df.copy()

    # ── 1. Derive trading date (timezone-safe) ────────────────────────────────
    out["_trading_date"] = pd.to_datetime(out["timestamp_utc"]).dt.date

    # ── 2. Aggregate per (date, session) — only named sessions ───────────────
    session_mask = out["session"].isin(_KNOWN_SESSIONS)
    agg_df = (
        out[session_mask]
        .groupby(["_trading_date", "session"], sort=False)
        .agg(_sh=("high", "max"), _sl=("low", "min"))
        .reset_index()
    )

    # ── 3. Pivot to wide format ───────────────────────────────────────────────
    if not agg_df.empty:
        pivot_h = agg_df.pivot(index="_trading_date", columns="session", values="_sh")
        pivot_l = agg_df.pivot(index="_trading_date", columns="session", values="_sl")
        pivot_h.columns = [f"session_high_{c.lower()}" for c in pivot_h.columns]
        pivot_l.columns = [f"session_low_{c.lower()}" for c in pivot_l.columns]
        session_levels = pd.concat([pivot_h, pivot_l], axis=1).reset_index()
        out = out.merge(session_levels, on="_trading_date", how="left")

    # ── 4. Ensure all per-session columns exist (fill NaN if a session absent) ─
    for sess in _KNOWN_SESSIONS:
        s = sess.lower()
        for prefix in ("session_high_", "session_low_"):
            col = f"{prefix}{s}"
            if col not in out.columns:
                out[col] = np.nan

    # ── 5. Vectorised session_high / session_low per bar ─────────────────────
    sess_col = out["session"]
    out["session_high"] = np.select(
        [sess_col == "ASIA", sess_col == "LONDON", sess_col == "NY"],
        [out["session_high_asia"], out["session_high_london"], out["session_high_ny"]],
        default=np.nan,
    )
    out["session_low"] = np.select(
        [sess_col == "ASIA", sess_col == "LONDON", sess_col == "NY"],
        [out["session_low_asia"], out["session_low_london"], out["session_low_ny"]],
        default=np.nan,
    )

    # ── 6. Clean up helper column ─────────────────────────────────────────────
    out = out.drop(columns=["_trading_date"])
    return out
