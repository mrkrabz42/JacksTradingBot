"""Screener commands: most-actives, movers."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, ApiBase
from bot.cli.formatting import console, output_json, make_table, format_money, format_pct

app = typer.Typer(no_args_is_help=True)


@app.command("most-actives")
def most_actives(
    by: str = typer.Option("volume", help="Rank by: volume, trades"),
    top: int = typer.Option(20, help="Number of results"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get most active stocks by volume or trade count."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/screener/stocks/most-actives",
        base=ApiBase.DATA,
        params={"by": by, "top": top},
    )

    if json_output:
        output_json(data)
        return

    actives = data.get("most_actives", [])
    if not actives:
        console.print("[dim]No data[/dim]")
        return

    rows = []
    for i, a in enumerate(actives, 1):
        rows.append((
            str(i),
            a.get("symbol", ""),
            f"{a.get('volume', 0):,}",
            str(a.get("trade_count", "")),
        ))

    table = make_table(
        title=f"Most Active Stocks (by {by})",
        columns=[
            {"name": "#", "justify": "right"}, {"name": "Symbol"},
            {"name": "Volume", "justify": "right"}, {"name": "Trades", "justify": "right"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command()
def movers(
    top: int = typer.Option(20, help="Number of results"),
    market_type: str = typer.Option("stocks", help="stocks or crypto"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get top market movers (gainers and losers)."""
    client = AlpacaClient()
    data = client.get(
        f"/v1beta1/screener/{market_type}/movers",
        base=ApiBase.DATA,
        params={"top": top},
    )

    if json_output:
        output_json(data)
        return

    for direction in ["gainers", "losers"]:
        items = data.get(direction, [])
        if not items:
            continue

        rows = []
        for i, m in enumerate(items, 1):
            rows.append((
                str(i),
                m.get("symbol", ""),
                format_money(m.get("price", 0)),
                format_pct(m.get("change", 0)),
                format_money(m.get("change", 0)),
                f"{m.get('volume', 0):,}" if m.get("volume") else "-",
            ))

        title_color = "[green]Gainers[/green]" if direction == "gainers" else "[red]Losers[/red]"
        table = make_table(
            title=f"Top {title_color}",
            columns=[
                {"name": "#", "justify": "right"}, {"name": "Symbol"},
                {"name": "Price", "justify": "right"}, {"name": "Change %", "justify": "right"},
                {"name": "Change $", "justify": "right"}, {"name": "Volume", "justify": "right"},
            ],
            rows=rows,
        )
        console.print(table)
        console.print()
