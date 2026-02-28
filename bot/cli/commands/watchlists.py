"""Watchlist commands: list, create, get, update, add-asset, delete, remove-symbol."""

from __future__ import annotations

from typing import Optional, List

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import console, output_json, make_table, error_msg, success_msg

app = typer.Typer(no_args_is_help=True)


def _print_watchlist(data: dict) -> None:
    """Pretty-print a watchlist."""
    console.print(f"\n[bold]{data.get('name', 'Unnamed')}[/bold] (ID: {data.get('id', '?')[:8]}...)")
    assets = data.get("assets", [])
    if assets:
        rows = [(a.get("symbol", ""), a.get("name", "")[:40], a.get("exchange", ""))
                for a in assets]
        table = make_table(
            title="",
            columns=[{"name": "Symbol"}, {"name": "Name"}, {"name": "Exchange"}],
            rows=rows,
        )
        console.print(table)
    else:
        console.print("  [dim]Empty watchlist[/dim]")


@app.command("list")
def list_watchlists(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List all watchlists."""
    client = AlpacaClient()
    data = client.get("/v2/watchlists")

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No watchlists[/dim]")
        return

    rows = []
    for w in data:
        asset_count = len(w.get("assets", []))
        rows.append((
            w.get("id", "")[:8] + "...",
            w.get("name", ""),
            str(asset_count),
            str(w.get("created_at", ""))[:19],
        ))

    table = make_table(
        title="Watchlists",
        columns=[{"name": "ID"}, {"name": "Name"}, {"name": "Assets", "justify": "right"},
                 {"name": "Created"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def create(
    name: str = typer.Argument(..., help="Watchlist name"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols to add"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Create a new watchlist."""
    body: dict = {"name": name}
    if symbols:
        body["symbols"] = [s.strip() for s in symbols.split(",")]

    client = AlpacaClient()
    data = client.post("/v2/watchlists", json=body)

    if json_output:
        output_json(data)
        return

    success_msg(f"Watchlist '{name}' created")
    _print_watchlist(data)


@app.command()
def get(
    watchlist_id: str = typer.Argument(..., help="Watchlist ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get a watchlist by ID."""
    client = AlpacaClient()
    data = client.get(f"/v2/watchlists/{watchlist_id}")

    if json_output:
        output_json(data)
        return

    _print_watchlist(data)


@app.command()
def update(
    watchlist_id: str = typer.Argument(..., help="Watchlist ID"),
    name: Optional[str] = typer.Option(None, help="New watchlist name"),
    symbols: Optional[str] = typer.Option(None, help="New symbols list (replaces existing)"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Update a watchlist (name and/or symbols)."""
    body: dict = {}
    if name:
        body["name"] = name
    if symbols:
        body["symbols"] = [s.strip() for s in symbols.split(",")]

    if not body:
        error_msg("Provide --name and/or --symbols to update")
        raise typer.Exit(1)

    client = AlpacaClient()
    data = client.put(f"/v2/watchlists/{watchlist_id}", json=body)

    if json_output:
        output_json(data)
        return

    success_msg("Watchlist updated")
    _print_watchlist(data)


@app.command("add-asset")
def add_asset(
    watchlist_id: str = typer.Argument(..., help="Watchlist ID"),
    symbol: str = typer.Argument(..., help="Symbol to add"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Add a symbol to a watchlist."""
    client = AlpacaClient()
    data = client.post(f"/v2/watchlists/{watchlist_id}", json={"symbol": symbol})

    if json_output:
        output_json(data)
        return

    success_msg(f"Added {symbol} to watchlist")
    _print_watchlist(data)


@app.command()
def delete(
    watchlist_id: str = typer.Argument(..., help="Watchlist ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Delete a watchlist."""
    client = AlpacaClient()
    client.delete(f"/v2/watchlists/{watchlist_id}")

    if json_output:
        output_json({"status": "deleted", "id": watchlist_id})
        return

    success_msg(f"Watchlist {watchlist_id} deleted")


@app.command("remove-symbol")
def remove_symbol(
    watchlist_id: str = typer.Argument(..., help="Watchlist ID"),
    symbol: str = typer.Argument(..., help="Symbol to remove"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Remove a symbol from a watchlist."""
    client = AlpacaClient()
    data = client.delete(f"/v2/watchlists/{watchlist_id}/{symbol}")

    if json_output:
        output_json(data or {"status": "removed", "symbol": symbol})
        return

    success_msg(f"Removed {symbol} from watchlist")
