"""Corporate actions commands: announcements."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import console, output_json, make_table

app = typer.Typer(no_args_is_help=True)


@app.command()
def announcements(
    ca_types: Optional[str] = typer.Option(None, "--types", help="Comma-separated types: dividend, merger, spinoff, split"),
    since: Optional[str] = typer.Option(None, help="Since date (YYYY-MM-DD)"),
    until: Optional[str] = typer.Option(None, help="Until date (YYYY-MM-DD)"),
    symbol: Optional[str] = typer.Option(None, help="Filter by symbol"),
    cusip: Optional[str] = typer.Option(None, help="Filter by CUSIP"),
    date_type: Optional[str] = typer.Option(None, "--date-type", help="declaration, ex, record, payable"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List corporate action announcements."""
    client = AlpacaClient()
    data = client.get(
        "/v2/corporate_actions/announcements",
        params={
            "ca_types": ca_types,
            "since": since,
            "until": until,
            "symbol": symbol,
            "cusip": cusip,
            "date_type": date_type,
        },
    )

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No announcements found[/dim]")
        return

    rows = []
    for a in data[:50]:
        rows.append((
            a.get("id", "")[:8] + "...",
            a.get("ca_type", ""),
            a.get("ca_sub_type", ""),
            a.get("initiating_symbol", a.get("symbol", "")),
            a.get("declaration_date", ""),
            a.get("ex_date", ""),
            a.get("record_date", ""),
        ))

    table = make_table(
        title=f"Corporate Actions ({len(data)} total)",
        columns=[
            {"name": "ID"}, {"name": "Type"}, {"name": "Sub Type"},
            {"name": "Symbol"}, {"name": "Declaration"}, {"name": "Ex Date"},
            {"name": "Record Date"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command("announcement")
def get_announcement(
    announcement_id: str = typer.Argument(..., help="Announcement ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get a specific corporate action announcement."""
    client = AlpacaClient()
    data = client.get(f"/v2/corporate_actions/announcements/{announcement_id}")

    if json_output:
        output_json(data)
        return

    rows = [(k, str(v)) for k, v in data.items()]
    table = make_table(
        title=f"Announcement: {announcement_id}",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)
