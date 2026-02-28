"""Market calendar and clock commands."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import console, output_json, make_table

app = typer.Typer(no_args_is_help=True)


@app.command()
def clock(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get current market clock (open/close times, status)."""
    client = AlpacaClient()
    data = client.get("/v2/clock")

    if json_output:
        output_json(data)
        return

    is_open = data.get("is_open", False)
    status = "[bold green]OPEN[/bold green]" if is_open else "[bold red]CLOSED[/bold red]"

    table = make_table(
        title="Market Clock",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=[
            ("Status", status),
            ("Timestamp", str(data.get("timestamp", ""))[:19]),
            ("Next Open", str(data.get("next_open", ""))[:19]),
            ("Next Close", str(data.get("next_close", ""))[:19]),
        ],
    )
    console.print(table)


@app.command("calendar")
def market_calendar(
    start: Optional[str] = typer.Option(None, help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, help="End date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get market calendar (trading days, open/close times)."""
    client = AlpacaClient()
    data = client.get("/v2/calendar", params={"start": start, "end": end})

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No calendar data[/dim]")
        return

    rows = []
    for d in data:
        rows.append((
            d.get("date", ""),
            d.get("open", ""),
            d.get("close", ""),
            d.get("session_open", ""),
            d.get("session_close", ""),
        ))

    table = make_table(
        title="Market Calendar",
        columns=[
            {"name": "Date"}, {"name": "Open"}, {"name": "Close"},
            {"name": "Session Open"}, {"name": "Session Close"},
        ],
        rows=rows,
    )
    console.print(table)
