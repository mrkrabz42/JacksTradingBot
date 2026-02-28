"""Session liquidity CLI commands — view session levels, classify timestamps."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer

from bot.cli.formatting import console, make_table, format_money, output_json, error_msg

app = typer.Typer(no_args_is_help=True)

DEFAULT_SYMBOL = "SPY"


@app.command()
def today(
    symbol: str = typer.Option(DEFAULT_SYMBOL, "--symbol", "-s", help="Ticker symbol"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Show today's session levels (highs/lows) with PDH/PDL."""
    from bot.sessions.extremes import get_full_session_report
    from bot.sessions.classifier import get_session_progress
    from bot.sessions.logger import log_session_levels

    now = datetime.utcnow()
    report = get_full_session_report(symbol, now)

    if json_output:
        output_json(report)
        return

    # Current session status
    progress = get_session_progress(now)
    console.print(f"\n[bold cyan]Session Status[/bold cyan]  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    if progress["session"] != "OUTSIDE":
        console.print(
            f"  Active: [bold]{progress['label']}[/bold] "
            f"({progress['start_utc']}–{progress['end_utc']} UTC) "
            f"[yellow]{progress['progress_pct']}%[/yellow] complete, "
            f"{progress['remaining_min']} min remaining"
        )
    else:
        console.print("  [dim]Outside all sessions[/dim]")

    # Session levels table
    sessions = report["sessions"]
    if sessions:
        table = make_table(
            title=f"Session Levels — {symbol} ({report['date']})",
            columns=[
                {"name": "Session"},
                {"name": "High", "justify": "right"},
                {"name": "High Time"},
                {"name": "Low", "justify": "right"},
                {"name": "Low Time"},
                {"name": "Bars", "justify": "right"},
            ],
            rows=[
                (
                    s["label"],
                    format_money(s["high"]) if s["high"] else "—",
                    _fmt_time(s["high_time"]),
                    format_money(s["low"]) if s["low"] else "—",
                    _fmt_time(s["low_time"]),
                    str(s["bar_count"]),
                )
                for s in sessions
            ],
        )
        console.print(table)

    # PDH/PDL
    daily = report["daily"]
    if daily.get("pdh") is not None:
        console.print(f"\n[bold cyan]Previous Day Levels[/bold cyan]  ({daily['date']})")
        pdh_table = make_table(
            title="",
            columns=[
                {"name": "Level"},
                {"name": "Price", "justify": "right"},
                {"name": "Session Owner"},
            ],
            rows=[
                ("[bold green]PDH[/bold green]", format_money(daily["pdh"]), daily.get("pdh_session", "")),
                ("[bold red]PDL[/bold red]", format_money(daily["pdl"]), daily.get("pdl_session", "")),
            ],
        )
        console.print(pdh_table)
    else:
        console.print("\n[dim]No previous day data available.[/dim]")

    # Log to CSV
    log_session_levels(symbol, report["date"], sessions, daily)
    console.print("\n[dim]Logged to bot/logs/session_levels.csv[/dim]")


@app.command()
def date(
    target_date: str = typer.Argument(..., help="Date in YYYY-MM-DD format"),
    symbol: str = typer.Option(DEFAULT_SYMBOL, "--symbol", "-s", help="Ticker symbol"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Show session levels for a specific date."""
    from bot.sessions.extremes import get_full_session_report

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        error_msg(f"Invalid date format: {target_date}. Use YYYY-MM-DD.")
        raise typer.Exit(1)

    report = get_full_session_report(symbol, dt)

    if json_output:
        output_json(report)
        return

    sessions = report["sessions"]
    if sessions:
        table = make_table(
            title=f"Session Levels — {symbol} ({report['date']})",
            columns=[
                {"name": "Session"},
                {"name": "High", "justify": "right"},
                {"name": "High Time"},
                {"name": "Low", "justify": "right"},
                {"name": "Low Time"},
                {"name": "Bars", "justify": "right"},
            ],
            rows=[
                (
                    s["label"],
                    format_money(s["high"]) if s["high"] else "—",
                    _fmt_time(s["high_time"]),
                    format_money(s["low"]) if s["low"] else "—",
                    _fmt_time(s["low_time"]),
                    str(s["bar_count"]),
                )
                for s in sessions
            ],
        )
        console.print(table)

    daily = report["daily"]
    if daily.get("pdh") is not None:
        console.print(f"\n[bold cyan]Previous Day Levels[/bold cyan]  ({daily['date']})")
        console.print(f"  PDH: {format_money(daily['pdh'])} ({daily.get('pdh_session', '')})")
        console.print(f"  PDL: {format_money(daily['pdl'])} ({daily.get('pdl_session', '')})")


@app.command()
def level(
    price: float = typer.Argument(..., help="Price to classify against session levels"),
    symbol: str = typer.Option(DEFAULT_SYMBOL, "--symbol", "-s", help="Ticker symbol"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Check where a price sits relative to today's session levels and PDH/PDL."""
    from bot.sessions.extremes import get_full_session_report

    now = datetime.utcnow()
    report = get_full_session_report(symbol, now)

    tags: list[str] = []
    daily = report["daily"]

    # Check PDH/PDL proximity (within 0.1%)
    if daily.get("pdh") is not None:
        pdh, pdl = daily["pdh"], daily["pdl"]
        threshold = 0.001

        if abs(price - pdh) / pdh < threshold:
            tags.append("AT PDH")
        elif price > pdh:
            tags.append("ABOVE PDH")

        if abs(price - pdl) / pdl < threshold:
            tags.append("AT PDL")
        elif price < pdl:
            tags.append("BELOW PDL")

    # Check session highs/lows
    for sess in report["sessions"]:
        if sess["high"] is None:
            continue
        h, l = sess["high"], sess["low"]
        name = sess["session"]
        threshold = 0.001

        if abs(price - h) / h < threshold:
            tags.append(f"AT {name} HIGH")
        if abs(price - l) / l < threshold:
            tags.append(f"AT {name} LOW")

    result = {
        "symbol": symbol,
        "price": price,
        "tags": tags,
        "pdh": daily.get("pdh"),
        "pdl": daily.get("pdl"),
    }

    if json_output:
        output_json(result)
        return

    console.print(f"\n[bold cyan]Level Check[/bold cyan]  {symbol} @ {format_money(price)}")
    if tags:
        for tag in tags:
            color = "green" if "HIGH" in tag or "PDH" in tag else "red" if "LOW" in tag or "PDL" in tag else "yellow"
            console.print(f"  [{color}]{tag}[/{color}]")
    else:
        console.print("  [dim]No notable session levels at this price.[/dim]")

    if daily.get("pdh") is not None:
        console.print(f"\n  PDH: {format_money(daily['pdh'])}  |  PDL: {format_money(daily['pdl'])}")


def _fmt_time(iso_str: Optional[str]) -> str:
    """Format an ISO timestamp to HH:MM UTC."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%H:%M UTC")
    except (ValueError, TypeError):
        return str(iso_str)
