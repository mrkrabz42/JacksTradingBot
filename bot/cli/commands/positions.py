"""Position commands: list, get, close, close-all, exercise."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import (
    console, output_json, make_table, format_money, format_pnl, format_pct,
    error_msg, success_msg,
)

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_positions(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List all open positions."""
    client = AlpacaClient()
    data = client.get("/v2/positions")

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No open positions[/dim]")
        return

    rows = []
    for p in data:
        rows.append((
            p.get("symbol", ""),
            p.get("side", ""),
            str(p.get("qty", "")),
            format_money(p.get("avg_entry_price", 0)),
            format_money(p.get("current_price", 0)),
            format_money(p.get("market_value", 0)),
            format_pnl(p.get("unrealized_pl", 0)),
            format_pct(p.get("unrealized_plpc", 0)),
            format_pnl(p.get("unrealized_intraday_pl", 0)),
        ))

    table = make_table(
        title="Open Positions",
        columns=[
            {"name": "Symbol"}, {"name": "Side"}, {"name": "Qty", "justify": "right"},
            {"name": "Entry", "justify": "right"}, {"name": "Current", "justify": "right"},
            {"name": "Mkt Value", "justify": "right"}, {"name": "P&L", "justify": "right"},
            {"name": "P&L %", "justify": "right"}, {"name": "Day P&L", "justify": "right"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command()
def get(
    symbol_or_id: str = typer.Argument(..., help="Symbol or asset ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get an open position by symbol or asset ID."""
    client = AlpacaClient()
    data = client.get(f"/v2/positions/{symbol_or_id}")

    if json_output:
        output_json(data)
        return

    rows = [
        ("Symbol", data.get("symbol", "")),
        ("Asset ID", data.get("asset_id", "")),
        ("Side", data.get("side", "")),
        ("Qty", str(data.get("qty", ""))),
        ("Avg Entry Price", format_money(data.get("avg_entry_price", 0))),
        ("Current Price", format_money(data.get("current_price", 0))),
        ("Market Value", format_money(data.get("market_value", 0))),
        ("Cost Basis", format_money(data.get("cost_basis", 0))),
        ("Unrealized P&L", format_pnl(data.get("unrealized_pl", 0))),
        ("Unrealized P&L %", format_pct(data.get("unrealized_plpc", 0))),
        ("Intraday P&L", format_pnl(data.get("unrealized_intraday_pl", 0))),
        ("Intraday P&L %", format_pct(data.get("unrealized_intraday_plpc", 0))),
    ]

    table = make_table(
        title=f"Position: {data.get('symbol', symbol_or_id)}",
        columns=[{"name": "Field"}, {"name": "Value", "justify": "right"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def close(
    symbol_or_id: str = typer.Argument(..., help="Symbol or asset ID"),
    qty: Optional[float] = typer.Option(None, help="Shares to close (partial close)"),
    percentage: Optional[float] = typer.Option(None, help="Percentage of position to close (0-100)"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Close a position (full or partial)."""
    params: dict = {}
    if qty is not None:
        params["qty"] = str(qty)
    if percentage is not None:
        params["percentage"] = str(percentage)

    client = AlpacaClient()
    data = client.delete(f"/v2/positions/{symbol_or_id}", params=params)

    if json_output:
        output_json(data)
        return

    success_msg(f"Position {symbol_or_id} close order submitted")
    if data:
        console.print(f"  Order ID: {data.get('id', '?')}")
        console.print(f"  Status: {data.get('status', '?')}")


@app.command("close-all")
def close_all(
    cancel_orders: bool = typer.Option(True, help="Also cancel open orders"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Close all open positions."""
    client = AlpacaClient()
    data = client.delete("/v2/positions", params={"cancel_orders": cancel_orders})

    if json_output:
        output_json(data or [])
        return

    if data:
        console.print(f"[bold green]Closing {len(data)} position(s)[/bold green]")
        for p in data:
            body = p.get("body", p)
            console.print(f"  {body.get('symbol', '?')} — Order ID: {body.get('id', '?')[:8]}...")
    else:
        console.print("[dim]No positions to close[/dim]")


@app.command()
def exercise(
    symbol_or_id: str = typer.Argument(..., help="Option contract symbol or ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Exercise an options position."""
    client = AlpacaClient()
    data = client.post(f"/v2/positions/{symbol_or_id}/exercise")

    if json_output:
        output_json(data or {"status": "exercised"})
        return

    success_msg(f"Exercise request submitted for {symbol_or_id}")
