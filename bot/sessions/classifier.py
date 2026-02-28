"""Session classifier — maps UTC timestamps to trading sessions."""

from __future__ import annotations

import json
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Tuple

_CONFIG_PATH = Path(__file__).parent / "config.json"

SessionName = str  # "ASIA" | "LONDON" | "NY" | "OUTSIDE"


def _load_sessions() -> Dict[str, Tuple[time, time, str]]:
    """Load session windows from config.json.

    Returns dict mapping session name -> (start_time, end_time, label).
    Start is inclusive, end is exclusive.
    """
    with open(_CONFIG_PATH) as f:
        cfg = json.load(f)

    sessions: Dict[str, Tuple[time, time, str]] = {}
    for name, info in cfg["sessions"].items():
        h_s, m_s = map(int, info["start_utc"].split(":"))
        h_e, m_e = map(int, info["end_utc"].split(":"))
        sessions[name] = (time(h_s, m_s), time(h_e, m_e), info["label"])
    return sessions


_SESSIONS = _load_sessions()


def get_session(timestamp_utc: datetime) -> SessionName:
    """Classify a UTC timestamp into a session name.

    Returns one of: 'ASIA', 'LONDON', 'NY', 'OUTSIDE'.
    Boundaries: start inclusive, end exclusive.
    """
    t = timestamp_utc.time()
    for name, (start, end, _label) in _SESSIONS.items():
        if start <= t < end:
            return name
    return "OUTSIDE"


def get_session_info(session_name: str) -> dict:
    """Return metadata for a session name.

    Returns dict with keys: start_utc, end_utc, label.
    Raises KeyError if session_name not found.
    """
    start, end, label = _SESSIONS[session_name]
    return {
        "start_utc": start.strftime("%H:%M"),
        "end_utc": end.strftime("%H:%M"),
        "label": label,
    }


def get_all_sessions() -> Dict[str, dict]:
    """Return info for all configured sessions."""
    return {name: get_session_info(name) for name in _SESSIONS}


def get_session_progress(timestamp_utc: datetime) -> dict:
    """Get progress through the current session.

    Returns dict with keys: session, label, progress_pct, elapsed_min,
    remaining_min, start_utc, end_utc.  If OUTSIDE any session, progress is 0.
    """
    session = get_session(timestamp_utc)
    if session == "OUTSIDE":
        return {
            "session": "OUTSIDE",
            "label": "Outside Sessions",
            "progress_pct": 0.0,
            "elapsed_min": 0,
            "remaining_min": 0,
            "start_utc": None,
            "end_utc": None,
        }

    start, end, label = _SESSIONS[session]
    now_minutes = timestamp_utc.hour * 60 + timestamp_utc.minute
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    total = end_minutes - start_minutes
    elapsed = now_minutes - start_minutes
    remaining = total - elapsed
    pct = (elapsed / total * 100) if total > 0 else 0.0

    return {
        "session": session,
        "label": label,
        "progress_pct": round(pct, 1),
        "elapsed_min": elapsed,
        "remaining_min": remaining,
        "start_utc": start.strftime("%H:%M"),
        "end_utc": end.strftime("%H:%M"),
    }
