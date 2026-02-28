"""Miscellaneous commands: logos, forex, corporate-actions (market data)."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, ApiBase
from bot.cli.formatting import console, output_json, make_table, format_money


def register(app: typer.Typer) -> None:
    """Register standalone commands and sub-apps on the root app."""
    app.add_typer(forex_app, name="forex", help="Forex rates")
    app.command(name="logo")(logo)
    app.command(name="corporate-actions-data")(corporate_actions_data)


# --- Forex sub-app ---
forex_app = typer.Typer(no_args_is_help=True)


@forex_app.command("latest")
def forex_latest(
    currency_pairs: str = typer.Argument(..., help="Comma-separated pairs (e.g., EUR/USD,GBP/USD)"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest forex rates."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/forex/latest/rates",
        base=ApiBase.DATA,
        params={"currency_pairs": currency_pairs},
    )

    if json_output:
        output_json(data)
        return

    rates = data.get("rates", {})
    rows = []
    for pair, rate_info in rates.items():
        rows.append((pair, str(rate_info.get("bp", "")), str(rate_info.get("ap", "")),
                      str(rate_info.get("mp", "")), str(rate_info.get("t", ""))[:19]))

    table = make_table(
        title="Latest Forex Rates",
        columns=[{"name": "Pair"}, {"name": "Bid", "justify": "right"},
                 {"name": "Ask", "justify": "right"}, {"name": "Mid", "justify": "right"},
                 {"name": "Time"}],
        rows=rows,
    )
    console.print(table)


@forex_app.command("history")
def forex_history(
    currency_pairs: str = typer.Argument(..., help="Comma-separated pairs"),
    timeframe: str = typer.Option("1Day", help="Timeframe"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical forex rates."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/forex/rates",
        base=ApiBase.DATA,
        params={"currency_pairs": currency_pairs, "timeframe": timeframe,
                "start": start, "end": end, "limit": limit},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


# --- Standalone commands ---
def logo(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get company logo URL for a symbol."""
    client = AlpacaClient()
    # The logo endpoint returns an image — we'll just provide the URL
    url = f"https://data.alpaca.markets/v1beta1/logos/{symbol}"
    if json_output:
        output_json({"symbol": symbol, "logo_url": url})
    else:
        console.print(f"[bold]{symbol}[/bold] logo URL: {url}")
        console.print("[dim]This URL returns the image directly. Open in browser or use curl.[/dim]")


def corporate_actions_data(
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols"),
    types: Optional[str] = typer.Option(None, help="Action types filter"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(50, help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get corporate actions from market data API."""
    client = AlpacaClient()
    data = client.get(
        "/v1/corporate-actions",
        base=ApiBase.DATA,
        params={"symbols": symbols, "types": types, "start": start, "end": end, "limit": limit},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)
