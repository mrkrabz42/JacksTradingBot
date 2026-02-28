"""Crypto market data commands: bars, quotes, trades, snapshots, orderbook."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, ApiBase
from bot.cli.formatting import console, output_json, make_table, format_money

app = typer.Typer(no_args_is_help=True)

# Crypto uses "us" locale by default
DEFAULT_LOC = "us"


@app.command()
def bars(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols (e.g., BTC/USD,ETH/USD)"),
    timeframe: str = typer.Option("1Day", help="1Min, 5Min, 15Min, 1Hour, 1Day, 1Week, 1Month"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max bars"),
    sort: str = typer.Option("desc", help="asc or desc"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical crypto bars."""
    client = AlpacaClient()
    data = client.get(
        f"/v1beta3/crypto/{loc}/bars",
        base=ApiBase.DATA,
        params={"symbols": symbols, "timeframe": timeframe, "start": start,
                "end": end, "limit": limit, "sort": sort},
    )

    if json_output:
        output_json(data)
        return

    bars_map = data.get("bars", {})
    for sym, bar_list in bars_map.items():
        rows = [(str(b.get("t", ""))[:19], format_money(b.get("o", 0)),
                 format_money(b.get("h", 0)), format_money(b.get("l", 0)),
                 format_money(b.get("c", 0)), f"{b.get('v', 0):,.4f}")
                for b in bar_list]
        table = make_table(
            title=f"{sym} Bars ({timeframe})",
            columns=[{"name": "Time"}, {"name": "Open", "justify": "right"},
                     {"name": "High", "justify": "right"}, {"name": "Low", "justify": "right"},
                     {"name": "Close", "justify": "right"}, {"name": "Volume", "justify": "right"}],
            rows=rows,
        )
        console.print(table)
        console.print()


@app.command("bars-latest")
def bars_latest(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest crypto bars."""
    client = AlpacaClient()
    data = client.get(f"/v1beta3/crypto/{loc}/latest/bars", base=ApiBase.DATA,
                      params={"symbols": symbols})

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("quotes")
def crypto_quotes(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max quotes"),
    sort: str = typer.Option("desc", help="asc or desc"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical crypto quotes."""
    client = AlpacaClient()
    data = client.get(
        f"/v1beta3/crypto/{loc}/quotes",
        base=ApiBase.DATA,
        params={"symbols": symbols, "start": start, "end": end, "limit": limit, "sort": sort},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("quotes-latest")
def quotes_latest(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest crypto quotes."""
    client = AlpacaClient()
    data = client.get(f"/v1beta3/crypto/{loc}/latest/quotes", base=ApiBase.DATA,
                      params={"symbols": symbols})

    if json_output:
        output_json(data)
        return

    quotes_map = data.get("quotes", {})
    rows = []
    for sym, q in quotes_map.items():
        rows.append((sym, format_money(q.get("bp", 0)), format_money(q.get("ap", 0)),
                      str(q.get("bs", "")), str(q.get("as", "")),
                      str(q.get("t", ""))[:19]))

    table = make_table(
        title="Latest Crypto Quotes",
        columns=[{"name": "Symbol"}, {"name": "Bid", "justify": "right"},
                 {"name": "Ask", "justify": "right"}, {"name": "Bid Sz", "justify": "right"},
                 {"name": "Ask Sz", "justify": "right"}, {"name": "Time"}],
        rows=rows,
    )
    console.print(table)


@app.command("trades")
def crypto_trades(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max trades"),
    sort: str = typer.Option("desc", help="asc or desc"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical crypto trades."""
    client = AlpacaClient()
    data = client.get(
        f"/v1beta3/crypto/{loc}/trades",
        base=ApiBase.DATA,
        params={"symbols": symbols, "start": start, "end": end, "limit": limit, "sort": sort},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("trades-latest")
def trades_latest(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest crypto trades."""
    client = AlpacaClient()
    data = client.get(f"/v1beta3/crypto/{loc}/latest/trades", base=ApiBase.DATA,
                      params={"symbols": symbols})

    if json_output:
        output_json(data)
        return

    trades_map = data.get("trades", {})
    rows = []
    for sym, t in trades_map.items():
        rows.append((sym, format_money(t.get("p", 0)), str(t.get("s", "")),
                      str(t.get("t", ""))[:19]))

    table = make_table(
        title="Latest Crypto Trades",
        columns=[{"name": "Symbol"}, {"name": "Price", "justify": "right"},
                 {"name": "Size", "justify": "right"}, {"name": "Time"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def snapshots(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get crypto snapshots."""
    client = AlpacaClient()
    data = client.get(f"/v1beta3/crypto/{loc}/snapshots", base=ApiBase.DATA,
                      params={"symbols": symbols})

    if json_output:
        output_json(data)
        return

    snap_map = data.get("snapshots", {})
    rows = []
    for sym, snap in snap_map.items():
        lt = snap.get("latestTrade", snap.get("latest_trade", {}))
        lq = snap.get("latestQuote", snap.get("latest_quote", {}))
        db = snap.get("dailyBar", snap.get("daily_bar", {}))
        rows.append((
            sym, format_money(lt.get("p", 0)),
            format_money(lq.get("bp", 0)), format_money(lq.get("ap", 0)),
            format_money(db.get("o", 0)), format_money(db.get("h", 0)),
            format_money(db.get("l", 0)),
        ))

    table = make_table(
        title="Crypto Snapshots",
        columns=[{"name": "Symbol"}, {"name": "Last", "justify": "right"},
                 {"name": "Bid", "justify": "right"}, {"name": "Ask", "justify": "right"},
                 {"name": "Open", "justify": "right"}, {"name": "High", "justify": "right"},
                 {"name": "Low", "justify": "right"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def orderbook(
    symbols: str = typer.Argument(..., help="Comma-separated crypto symbols"),
    loc: str = typer.Option(DEFAULT_LOC, help="Locale: us"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest crypto orderbook."""
    client = AlpacaClient()
    data = client.get(f"/v1beta3/crypto/{loc}/latest/orderbooks", base=ApiBase.DATA,
                      params={"symbols": symbols})

    if json_output:
        output_json(data)
        return

    orderbooks = data.get("orderbooks", {})
    for sym, ob in orderbooks.items():
        console.print(f"\n[bold]{sym} Orderbook[/bold]")
        bids = ob.get("b", [])[:10]
        asks = ob.get("a", [])[:10]

        rows = []
        for i in range(max(len(bids), len(asks))):
            bid_p = format_money(bids[i].get("p", 0)) if i < len(bids) else ""
            bid_s = str(bids[i].get("s", "")) if i < len(bids) else ""
            ask_p = format_money(asks[i].get("p", 0)) if i < len(asks) else ""
            ask_s = str(asks[i].get("s", "")) if i < len(asks) else ""
            rows.append((bid_s, bid_p, ask_p, ask_s))

        table = make_table(
            title="",
            columns=[{"name": "Bid Size", "justify": "right"}, {"name": "Bid", "justify": "right"},
                     {"name": "Ask", "justify": "right"}, {"name": "Ask Size", "justify": "right"}],
            rows=rows,
        )
        console.print(table)
