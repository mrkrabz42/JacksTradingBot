"""Asset commands: list, get, option contracts."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import console, output_json, make_table, format_status

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_assets(
    status: str = typer.Option("active", help="active or inactive"),
    asset_class: Optional[str] = typer.Option(None, "--class", help="us_equity, crypto, us_option"),
    exchange: Optional[str] = typer.Option(None, help="Exchange filter (e.g., NYSE, NASDAQ)"),
    attributes: Optional[str] = typer.Option(None, help="Comma-separated attributes filter"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List tradable assets."""
    client = AlpacaClient()
    data = client.get(
        "/v2/assets",
        params={
            "status": status,
            "asset_class": asset_class,
            "exchange": exchange,
            "attributes": attributes,
        },
    )

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No assets found[/dim]")
        return

    # Show first 50 to avoid overwhelming output
    shown = data[:50]
    rows = []
    for a in shown:
        rows.append((
            a.get("symbol", ""),
            a.get("name", "")[:40],
            a.get("exchange", ""),
            a.get("class", ""),
            "Yes" if a.get("tradable") else "No",
            "Yes" if a.get("fractionable") else "No",
            "Yes" if a.get("shortable") else "No",
        ))

    table = make_table(
        title=f"Assets ({len(shown)} of {len(data)})",
        columns=[
            {"name": "Symbol"}, {"name": "Name"}, {"name": "Exchange"},
            {"name": "Class"}, {"name": "Tradable"}, {"name": "Fractional"},
            {"name": "Shortable"},
        ],
        rows=rows,
    )
    console.print(table)
    if len(data) > 50:
        console.print(f"[dim]... and {len(data) - 50} more. Use --json for full output.[/dim]")


@app.command()
def get(
    symbol_or_id: str = typer.Argument(..., help="Symbol or asset ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get asset details by symbol or ID."""
    client = AlpacaClient()
    data = client.get(f"/v2/assets/{symbol_or_id}")

    if json_output:
        output_json(data)
        return

    rows = [
        ("Symbol", data.get("symbol", "")),
        ("Name", data.get("name", "")),
        ("Asset ID", data.get("id", "")),
        ("Class", data.get("class", "")),
        ("Exchange", data.get("exchange", "")),
        ("Status", data.get("status", "")),
        ("Tradable", str(data.get("tradable", ""))),
        ("Marginable", str(data.get("marginable", ""))),
        ("Shortable", str(data.get("shortable", ""))),
        ("Fractionable", str(data.get("fractionable", ""))),
        ("Easy to Borrow", str(data.get("easy_to_borrow", ""))),
        ("Min Order Size", str(data.get("min_order_size", ""))),
        ("Min Trade Increment", str(data.get("min_trade_increment", ""))),
        ("Price Increment", str(data.get("price_increment", ""))),
    ]

    table = make_table(
        title=f"Asset: {data.get('symbol', symbol_or_id)}",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)


@app.command("options-contracts")
def options_contracts(
    underlying_symbols: Optional[str] = typer.Option(None, "--symbols", help="Underlying symbols (comma-separated)"),
    status: str = typer.Option("active", help="active or inactive"),
    expiration_date: Optional[str] = typer.Option(None, "--expiry", help="Expiration date (YYYY-MM-DD) or range with gte/lte"),
    expiration_date_gte: Optional[str] = typer.Option(None, "--expiry-gte", help="Expiry date >= (YYYY-MM-DD)"),
    expiration_date_lte: Optional[str] = typer.Option(None, "--expiry-lte", help="Expiry date <= (YYYY-MM-DD)"),
    strike_price_gte: Optional[float] = typer.Option(None, "--strike-gte", help="Strike price >="),
    strike_price_lte: Optional[float] = typer.Option(None, "--strike-lte", help="Strike price <="),
    root_symbol: Optional[str] = typer.Option(None, help="Root symbol filter"),
    option_type: Optional[str] = typer.Option(None, "--type", help="call or put"),
    limit: int = typer.Option(50, help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List option contracts."""
    client = AlpacaClient()
    data = client.get(
        "/v2/options/contracts",
        params={
            "underlying_symbols": underlying_symbols,
            "status": status,
            "expiration_date": expiration_date,
            "expiration_date_gte": expiration_date_gte,
            "expiration_date_lte": expiration_date_lte,
            "strike_price_gte": str(strike_price_gte) if strike_price_gte else None,
            "strike_price_lte": str(strike_price_lte) if strike_price_lte else None,
            "root_symbol": root_symbol,
            "type": option_type,
            "limit": limit,
        },
    )

    if json_output:
        output_json(data)
        return

    contracts = data.get("option_contracts", data) if isinstance(data, dict) else data
    if not contracts or (isinstance(contracts, dict) and not contracts):
        console.print("[dim]No option contracts found[/dim]")
        return

    if isinstance(contracts, list):
        rows = []
        for c in contracts[:50]:
            rows.append((
                c.get("symbol", ""),
                c.get("underlying_symbol", ""),
                c.get("type", ""),
                str(c.get("strike_price", "")),
                c.get("expiration_date", ""),
                c.get("status", ""),
            ))

        table = make_table(
            title="Option Contracts",
            columns=[
                {"name": "Symbol"}, {"name": "Underlying"}, {"name": "Type"},
                {"name": "Strike", "justify": "right"}, {"name": "Expiry"}, {"name": "Status"},
            ],
            rows=rows,
        )
        console.print(table)
    else:
        console.print_json(data=data)


@app.command("options-contract")
def options_contract(
    symbol_or_id: str = typer.Argument(..., help="Option contract symbol or ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get a specific option contract."""
    client = AlpacaClient()
    data = client.get(f"/v2/options/contracts/{symbol_or_id}")

    if json_output:
        output_json(data)
        return

    rows = [(k, str(v)) for k, v in data.items()]
    table = make_table(
        title=f"Option Contract: {symbol_or_id}",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)
