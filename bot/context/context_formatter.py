"""Context formatter — converts engine numeric outputs to human-readable text."""
from __future__ import annotations

import math
from typing import Any

from bot.structure.config import ContextFormatterConfig


# ── Utility ───────────────────────────────────────────────────────────────────

def _get(snap: dict, key: str) -> Any:
    """Return snap[key], or None if absent / None / NaN."""
    val = snap.get(key)
    if val is None:
        return None
    try:
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    return val


# ── Per-dimension flag helpers ────────────────────────────────────────────────

def _trend_flags(snap: dict, cfg: ContextFormatterConfig) -> list[str]:
    regime = _get(snap, "regime")
    direction = _get(snap, "trend_direction")
    score = _get(snap, "trend_strength_score") or 0.0

    if regime == "TREND":
        if direction == "UP" and score >= cfg.trend_moderate_max:
            return ["TRENDING UP"]
        if direction == "DOWN" and score >= cfg.trend_moderate_max:
            return ["TRENDING DOWN"]
    if regime == "RANGE":
        return ["RANGE-BOUND"]
    if score < cfg.trend_weak_max and regime not in ("TREND", "RANGE"):
        return ["WEAK TREND"]
    if regime is None or regime == "TRANSITION":
        if direction == "UP":
            return ["MILD UP BIAS"]
        if direction == "DOWN":
            return ["MILD DOWN BIAS"]
    return []


def _volatility_flags(snap: dict, cfg: ContextFormatterConfig) -> list[str]:
    state = _get(snap, "volatility_state")
    if state == "LOW":
        return ["LOW VOLATILITY"]
    if state == "HIGH":
        return ["HIGH VOLATILITY"]
    return []  # MEDIUM → omit


def _liquidity_flags(snap: dict, cfg: ContextFormatterConfig) -> list[str]:
    direction = _get(snap, "liquidity_draw_direction")
    score = _get(snap, "liquidity_magnet_score") or 0.0
    dist_sh = _get(snap, "dist_session_high")
    dist_sl = _get(snap, "dist_session_low")

    # Session proximity check first
    if dist_sh is not None and direction == "ABOVE":
        try:
            if 0 <= float(dist_sh) < cfg.session_near_atr:
                return ["NEAR SESSION HIGH"]
        except (TypeError, ValueError):
            pass
    if dist_sl is not None and direction == "BELOW":
        try:
            if abs(float(dist_sl)) < cfg.session_near_atr:
                return ["NEAR SESSION LOW"]
        except (TypeError, ValueError):
            pass

    if direction == "ABOVE":
        if score >= cfg.liq_strong_min:
            return ["LIQUIDITY PULL ABOVE"]
        if cfg.liq_weak_max <= score < cfg.liq_strong_min:
            return ["MILD LIQUIDITY PULL ABOVE"]
    elif direction == "BELOW":
        if score >= cfg.liq_strong_min:
            return ["LIQUIDITY PULL BELOW"]
        if cfg.liq_weak_max <= score < cfg.liq_strong_min:
            return ["MILD LIQUIDITY PULL BELOW"]
    return []


def _mtf_flags(snap: dict, cfg: ContextFormatterConfig) -> list[str]:
    state = _get(snap, "mtf_alignment_state")
    score = _get(snap, "mtf_alignment_score") or 0.0

    if state in ("FULL_ALIGN_UP", "PARTIAL_ALIGN_UP"):
        if state == "FULL_ALIGN_UP" or score >= cfg.mtf_strong_min:
            return ["MTF ALIGN UP"]
        if score >= cfg.mtf_weak_max:
            return ["PARTIAL MTF ALIGNMENT"]
    elif state in ("FULL_ALIGN_DOWN", "PARTIAL_ALIGN_DOWN"):
        if state == "FULL_ALIGN_DOWN" or score >= cfg.mtf_strong_min:
            return ["MTF ALIGN DOWN"]
        if score >= cfg.mtf_weak_max:
            return ["PARTIAL MTF ALIGNMENT"]
    elif state == "CONFLICT":
        return ["MIXED MTF CONTEXT"]
    # WEAK_ALIGN → omit
    return []


def _participation_flags(snap: dict, cfg: ContextFormatterConfig) -> list[str]:
    state = _get(snap, "participation_state")
    rvol = _get(snap, "rvol_ratio")
    vol_state = _get(snap, "volume_state")
    flags: list[str] = []

    rvol_val = float(rvol) if rvol is not None else 1.0

    if state == "EXTREME" or rvol_val >= cfg.rvol_extreme_min:
        flags.append("AGGRESSIVE PARTICIPATION")
    elif state == "ELEVATED" or rvol_val >= cfg.rvol_high_min:
        flags.append("ELEVATED PARTICIPATION")
    elif state == "LOW_ACTIVITY" or rvol_val <= cfg.rvol_low_max:
        flags.append("QUIET TAPE")

    if vol_state == "ACCEPTING_ABOVE":
        flags.append("PRICE ACCEPTING ABOVE VALUE")
    elif vol_state == "ACCEPTING_BELOW":
        flags.append("PRICE ACCEPTING BELOW VALUE")

    return flags


def _breakout_flags(snap: dict, cfg: ContextFormatterConfig) -> list[str]:
    btype = _get(snap, "breakout_type")
    score = _get(snap, "breakout_quality_score") or 0.0

    if btype == "CONTINUATION":
        if score >= cfg.bkt_strong_min:
            return ["BREAKOUT CONTINUATION"]
        if score >= cfg.bkt_weak_max:
            return ["POTENTIAL BREAKOUT CONTINUATION"]
    elif btype == "FAKEOUT":
        if score > cfg.bkt_weak_max:
            return ["FAKEOUT WARNING"]
    elif btype == "UNCLEAR":
        if score >= cfg.bkt_weak_max:
            return ["POTENTIAL BREAKOUT"]
    return []


def _confluence_flags(snap: dict, event: dict, cfg: ContextFormatterConfig) -> list[str]:
    grade = (
        event.get("event_grade")
        or event.get("setup_grade")
        or _get(snap, "setup_grade")
    )
    score = (
        event.get("event_confluence_score")
        or event.get("confluence_score")
        or _get(snap, "confluence_score")
        or 0.0
    )

    if grade == "A_PLUS_SETUP":
        return ["A+ CONTEXT"]
    if grade == "HIGH_SETUP":
        return ["A CONTEXT"]
    if grade == "MEDIUM_SETUP":
        return ["B CONTEXT"]

    # No grade — fall back to score
    score = float(score)
    if score >= cfg.conf_strong_min:
        return ["HIGH CONFLUENCE"]
    if score >= cfg.conf_weak_max:
        return ["MODERATE CONFLUENCE"]
    return []


def _bias_flags(snap: dict, event: dict, cfg: ContextFormatterConfig) -> list[str]:
    direction = (
        event.get("direction")
        or event.get("entry_bias")
        or _get(snap, "bar_trade_bias")
    )
    if not direction:
        return []

    long_dir = direction in ("BULL", "LONG", "UP")
    short_dir = direction in ("BEAR", "SHORT", "DOWN")
    if not long_dir and not short_dir:
        return []

    trend_dir = _get(snap, "trend_direction")
    mtf_state = _get(snap, "mtf_alignment_state") or ""
    liq_dir = _get(snap, "liquidity_draw_direction")

    factors = 0
    if long_dir:
        if trend_dir == "UP":
            factors += 1
        if "UP" in mtf_state:
            factors += 1
        if liq_dir == "ABOVE":
            factors += 1
    else:
        if trend_dir == "DOWN":
            factors += 1
        if "DOWN" in mtf_state:
            factors += 1
        if liq_dir == "BELOW":
            factors += 1

    if factors >= cfg.strong_bias_threshold:
        return ["STRONG LONG BIAS"] if long_dir else ["STRONG SHORT BIAS"]
    if factors >= 1:
        return ["LONG BIAS"] if long_dir else ["SHORT BIAS"]
    return []


def _session_flags(snap: dict) -> list[str]:
    session = _get(snap, "session")
    mapping = {
        "ASIA": "ASIA SESSION",
        "LONDON": "LONDON SESSION",
        "NY": "NEW YORK SESSION",
    }
    tag = mapping.get(session or "")
    return [tag] if tag else []


# ── Public: build_context_flags ───────────────────────────────────────────────

def build_context_flags(
    snapshot: "pd.Series | dict",
    event: dict | None = None,
    config: ContextFormatterConfig | None = None,
) -> list[str]:
    """Return an ordered, deduplicated list of context flag strings."""
    cfg = config or ContextFormatterConfig()
    snap: dict = snapshot if isinstance(snapshot, dict) else snapshot.to_dict()
    evt = event or {}

    raw: list[str] = []
    raw.extend(_trend_flags(snap, cfg))
    raw.extend(_volatility_flags(snap, cfg))
    raw.extend(_liquidity_flags(snap, cfg))
    raw.extend(_mtf_flags(snap, cfg))
    raw.extend(_participation_flags(snap, cfg))
    raw.extend(_breakout_flags(snap, cfg))
    raw.extend(_confluence_flags(snap, evt, cfg))
    raw.extend(_bias_flags(snap, evt, cfg))
    raw.extend(_session_flags(snap))

    seen: set[str] = set()
    result: list[str] = []
    for f in raw:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result[: cfg.max_flags]


# ── Summary clause helpers ────────────────────────────────────────────────────

def _summary_trend_vol_clause(snap: dict, cfg: ContextFormatterConfig) -> str | None:
    regime = _get(snap, "regime")
    direction = _get(snap, "trend_direction")
    score = float(_get(snap, "trend_strength_score") or 0)
    vol = _get(snap, "volatility_state")

    # Trend phrase
    if regime == "RANGE":
        trend_phrase = "range-bound conditions"
    elif regime == "TREND" and direction == "UP":
        trend_phrase = "strong uptrend" if score >= cfg.trend_moderate_max else "uptrend"
    elif regime == "TREND" and direction == "DOWN":
        trend_phrase = "strong downtrend" if score >= cfg.trend_moderate_max else "downtrend"
    elif direction == "UP":
        trend_phrase = "mild upward bias"
    elif direction == "DOWN":
        trend_phrase = "mild downward bias"
    else:
        trend_phrase = "weak trend"

    # Volatility phrase
    vol_map = {"LOW": "low volatility", "MEDIUM": "normal volatility", "HIGH": "high volatility"}
    vol_phrase = vol_map.get(vol or "", "")

    if vol_phrase:
        return f"{trend_phrase} with {vol_phrase}"
    return trend_phrase


def _summary_liquidity_mtf_clause(snap: dict, cfg: ContextFormatterConfig) -> str | None:
    direction = _get(snap, "liquidity_draw_direction")
    score = float(_get(snap, "liquidity_magnet_score") or 0)
    dist_sh = _get(snap, "dist_session_high")
    dist_sl = _get(snap, "dist_session_low")
    mtf_state = _get(snap, "mtf_alignment_state") or ""
    mtf_score = float(_get(snap, "mtf_alignment_score") or 0)

    # Liquidity phrase
    liq_phrase: str | None = None
    try:
        if dist_sh is not None and direction == "ABOVE" and 0 <= float(dist_sh) < cfg.session_near_atr:
            liq_phrase = "near session high"
        elif dist_sl is not None and direction == "BELOW" and abs(float(dist_sl)) < cfg.session_near_atr:
            liq_phrase = "near session low"
    except (TypeError, ValueError):
        pass

    if liq_phrase is None:
        if direction == "ABOVE":
            liq_phrase = "liquidity drawing above" if score >= cfg.liq_strong_min else "mild liquidity pull above"
        elif direction == "BELOW":
            liq_phrase = "liquidity drawing below" if score >= cfg.liq_strong_min else "mild liquidity pull below"
        else:
            liq_phrase = "balanced liquidity"

    # MTF phrase
    mtf_phrase: str | None = None
    if "FULL_ALIGN_UP" in mtf_state or ("UP" in mtf_state and mtf_score >= cfg.mtf_strong_min):
        mtf_phrase = "multi-timeframe alignment up"
    elif "FULL_ALIGN_DOWN" in mtf_state or ("DOWN" in mtf_state and mtf_score >= cfg.mtf_strong_min):
        mtf_phrase = "bearish multi-timeframe alignment"
    elif "PARTIAL" in mtf_state:
        mtf_phrase = "partial multi-timeframe alignment"
    elif "CONFLICT" in mtf_state:
        mtf_phrase = "mixed multi-timeframe context"

    if liq_phrase and mtf_phrase:
        return f"{liq_phrase} and {mtf_phrase}"
    return liq_phrase or mtf_phrase


def _summary_participation_clause(snap: dict, cfg: ContextFormatterConfig) -> str | None:
    state = _get(snap, "participation_state")
    rvol = _get(snap, "rvol_ratio")
    spike = _get(snap, "volume_spike_flag")

    rvol_val = float(rvol) if rvol is not None else 1.0

    if state == "EXTREME" or rvol_val >= cfg.rvol_extreme_min:
        if spike:
            return "aggressive participation with volume spike"
        return "aggressive participation and above-average volume"
    if state == "ELEVATED" or rvol_val >= cfg.rvol_high_min:
        return "elevated participation and above-average volume"
    if state == "LOW_ACTIVITY" or rvol_val <= cfg.rvol_low_max:
        return "muted participation and below-average volume"
    return None  # NORMAL → omit


def _summary_setup_clause(snap: dict, event: dict, cfg: ContextFormatterConfig) -> str | None:
    grade = (
        event.get("event_grade")
        or event.get("setup_grade")
        or _get(snap, "setup_grade")
    )
    score = float(
        event.get("event_confluence_score")
        or event.get("confluence_score")
        or _get(snap, "confluence_score")
        or 0
    )

    direction = (
        event.get("direction")
        or event.get("entry_bias")
        or _get(snap, "bar_trade_bias")
        or ""
    )
    long_dir = direction in ("BULL", "LONG", "UP")
    short_dir = direction in ("BEAR", "SHORT", "DOWN")
    bias_phrase = "long" if long_dir else "short" if short_dir else ""

    if grade == "A_PLUS_SETUP":
        base = f"A+ {bias_phrase} context" if bias_phrase else "A+ context"
        return f"{base} with high confluence and clear continuation bias"
    if grade == "HIGH_SETUP":
        base = f"A-grade {bias_phrase} opportunity" if bias_phrase else "A-grade opportunity"
        return f"{base} with strong confluence"
    if grade == "MEDIUM_SETUP":
        return "B-grade setup in a mixed environment"
    if score < cfg.conf_weak_max:
        return "low-confluence environment — no clear setup"
    return None


# ── Public: build_environment_summary ────────────────────────────────────────

def build_environment_summary(
    snapshot: "pd.Series | dict",
    event: dict | None = None,
    config: ContextFormatterConfig | None = None,
) -> str:
    """Return a single natural-language sentence describing the market context."""
    cfg = config or ContextFormatterConfig()
    snap: dict = snapshot if isinstance(snapshot, dict) else snapshot.to_dict()
    evt = event or {}

    c1 = _summary_trend_vol_clause(snap, cfg)
    c2 = _summary_liquidity_mtf_clause(snap, cfg)
    c3 = _summary_participation_clause(snap, cfg)
    c4 = _summary_setup_clause(snap, evt, cfg)

    parts = [c for c in [c1, c2, c3, c4] if c]
    sentence = ", ".join(parts)
    if sentence:
        sentence = sentence[0].upper() + sentence[1:]
    if len(sentence) > cfg.summary_max_chars:
        sentence = sentence[: cfg.summary_max_chars - 3].rstrip(", ") + "..."
    return sentence
