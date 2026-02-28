"""Rich-based output formatting for CLI commands."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional, Sequence

from rich.console import Console
from rich.table import Table

console = Console()
error_console = Console(stderr=True)


def output_json(data: Any) -> None:
    """Print raw JSON to stdout (for --json mode)."""
    sys.stdout.write(json.dumps(data, indent=2, default=str) + "\n")


def make_table(
    title: str,
    columns: List[Dict[str, Any]],
    rows: List[Sequence[str]],
) -> Table:
    """Build a Rich table."""
    table = Table(title=title, show_lines=False, padding=(0, 1))
    for col in columns:
        table.add_column(
            col["name"],
            style=col.get("style"),
            justify=col.get("justify", "left"),
        )
    for row in rows:
        table.add_row(*[str(x) for x in row])
    return table


def format_money(value: Any) -> str:
    """Format as $1,234.56."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_pnl(value: Any) -> str:
    """Format P&L with color: green positive, red negative."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v >= 0:
        return f"[green]+${v:,.2f}[/green]"
    return f"[red]-${abs(v):,.2f}[/red]"


def format_pct(value: Any) -> str:
    """Format percentage with color."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    pct = v * 100 if abs(v) < 1 else v
    if pct >= 0:
        return f"[green]+{pct:.2f}%[/green]"
    return f"[red]{pct:.2f}%[/red]"


def format_status(status: str) -> str:
    """Color-code order/position status."""
    colors = {
        "new": "cyan",
        "accepted": "cyan",
        "pending_new": "yellow",
        "partially_filled": "yellow",
        "filled": "green",
        "done_for_day": "blue",
        "canceled": "dim",
        "expired": "dim",
        "replaced": "dim",
        "rejected": "red",
        "suspended": "red",
        "active": "green",
    }
    color = colors.get(status.lower(), "white")
    return f"[{color}]{status}[/{color}]"


def error_msg(message: str) -> None:
    """Print an error message to stderr."""
    error_console.print(f"[bold red]Error:[/bold red] {message}")


def success_msg(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]OK:[/bold green] {message}")


def warning_msg(message: str) -> None:
    """Print a warning."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")
