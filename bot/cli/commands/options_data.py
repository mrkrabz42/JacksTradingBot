"""Options market data commands: bars, quotes, trades, snapshots, chain, meta."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, ApiBase
from bot.cli.formatting import console, output_json, make_table, format_money

app = typer.Typer(no_args_is_help=True)


@app.command()
def bars(
    symbols: str = typer.Argument(..., help="Comma-separated option contract symbols"),
    timeframe: str = typer.Option("1Day", help="1Min, 5Min, 15Min, 1Hour, 1Day, 1Week, 1Month"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max bars"),
    sort: str = typer.Option("desc", help="asc or desc"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical options bars."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/options/bars",
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
                 format_money(b.get("c", 0)), str(b.get("v", 0)))
                for b in bar_list]
        table = make_table(
            title=f"{sym} Option Bars",
            columns=[{"name": "Time"}, {"name": "Open", "justify": "right"},
                     {"name": "High", "justify": "right"}, {"name": "Low", "justify": "right"},
                     {"name": "Close", "justify": "right"}, {"name": "Volume", "justify": "right"}],
            rows=rows,
        )
        console.print(table)
        console.print()


@app.command("quotes-latest")
def quotes_latest(
    symbols: str = typer.Argument(..., help="Comma-separated option symbols"),
    feed: str = typer.Option("indicative", help="indicative or opra"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest option quotes."""
    client = AlpacaClient()
    data = client.get("/v1beta1/options/quotes/latest", base=ApiBase.DATA,
                      params={"symbols": symbols, "feed": feed})

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
        title="Latest Option Quotes",
        columns=[{"name": "Symbol"}, {"name": "Bid", "justify": "right"},
                 {"name": "Ask", "justify": "right"}, {"name": "Bid Sz", "justify": "right"},
                 {"name": "Ask Sz", "justify": "right"}, {"name": "Time"}],
        rows=rows,
    )
    console.print(table)


@app.command("trades")
def option_trades(
    symbols: str = typer.Argument(..., help="Comma-separated option symbols"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max trades"),
    sort: str = typer.Option("desc", help="asc or desc"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical option trades."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/options/trades",
        base=ApiBase.DATA,
        params={"symbols": symbols, "start": start, "end": end, "limit": limit, "sort": sort},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("trades-latest")
def trades_latest(
    symbols: str = typer.Argument(..., help="Comma-separated option symbols"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest option trades."""
    client = AlpacaClient()
    data = client.get("/v1beta1/options/trades/latest", base=ApiBase.DATA,
                      params={"symbols": symbols})

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command()
def snapshots(
    symbols: str = typer.Argument(..., help="Comma-separated option symbols"),
    feed: str = typer.Option("indicative", help="indicative or opra"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get option snapshots."""
    client = AlpacaClient()
    data = client.get("/v1beta1/options/snapshots", base=ApiBase.DATA,
                      params={"symbols": symbols, "feed": feed})

    if json_output:
        output_json(data)
        return

    snap_map = data.get("snapshots", {})
    for sym, snap in snap_map.items():
        lq = snap.get("latestQuote", snap.get("latest_quote", {}))
        lt = snap.get("latestTrade", snap.get("latest_trade", {}))
        greeks = snap.get("greeks", {})

        rows = [
            ("Latest Trade", f"{format_money(lt.get('p', 0))} x {lt.get('s', '?')}"),
            ("Bid", f"{format_money(lq.get('bp', 0))} x {lq.get('bs', '?')}"),
            ("Ask", f"{format_money(lq.get('ap', 0))} x {lq.get('as', '?')}"),
            ("Implied Vol", f"{snap.get('impliedVolatility', snap.get('implied_volatility', 'N/A'))}"),
        ]
        if greeks:
            rows.extend([
                ("Delta", str(greeks.get("delta", ""))),
                ("Gamma", str(greeks.get("gamma", ""))),
                ("Theta", str(greeks.get("theta", ""))),
                ("Vega", str(greeks.get("vega", ""))),
                ("Rho", str(greeks.get("rho", ""))),
            ])

        table = make_table(
            title=f"{sym} Snapshot",
            columns=[{"name": "Field"}, {"name": "Value", "justify": "right"}],
            rows=rows,
        )
        console.print(table)
        console.print()


@app.command()
def chain(
    underlying_symbol: str = typer.Argument(..., help="Underlying symbol (e.g., AAPL)"),
    feed: str = typer.Option("indicative", help="indicative or opra"),
    expiration_date: Optional[str] = typer.Option(None, "--expiry", help="Expiration date (YYYY-MM-DD)"),
    expiration_date_gte: Optional[str] = typer.Option(None, "--expiry-gte", help="Expiry date >="),
    expiration_date_lte: Optional[str] = typer.Option(None, "--expiry-lte", help="Expiry date <="),
    strike_price_gte: Optional[float] = typer.Option(None, "--strike-gte", help="Strike >="),
    strike_price_lte: Optional[float] = typer.Option(None, "--strike-lte", help="Strike <="),
    option_type: Optional[str] = typer.Option(None, "--type", help="call or put"),
    limit: int = typer.Option(50, help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get option chain for an underlying symbol."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/options/snapshots",
        base=ApiBase.DATA,
        params={
            "underlying_symbols": underlying_symbol,
            "feed": feed,
            "expiration_date": expiration_date,
            "expiration_date_gte": expiration_date_gte,
            "expiration_date_lte": expiration_date_lte,
            "strike_price_gte": str(strike_price_gte) if strike_price_gte else None,
            "strike_price_lte": str(strike_price_lte) if strike_price_lte else None,
            "type": option_type,
            "limit": limit,
        },
    )

    if json_output:
        output_json(data)
        return

    snap_map = data.get("snapshots", {})
    if not snap_map:
        console.print("[dim]No option chain data[/dim]")
        return

    rows = []
    for sym, snap in snap_map.items():
        lq = snap.get("latestQuote", snap.get("latest_quote", {}))
        greeks = snap.get("greeks", {})
        rows.append((
            sym,
            format_money(lq.get("bp", 0)),
            format_money(lq.get("ap", 0)),
            str(snap.get("impliedVolatility", snap.get("implied_volatility", ""))),
            str(greeks.get("delta", "")),
            str(greeks.get("gamma", "")),
            str(greeks.get("theta", "")),
        ))

    table = make_table(
        title=f"Option Chain: {underlying_symbol}",
        columns=[
            {"name": "Contract"}, {"name": "Bid", "justify": "right"},
            {"name": "Ask", "justify": "right"}, {"name": "IV", "justify": "right"},
            {"name": "Delta", "justify": "right"}, {"name": "Gamma", "justify": "right"},
            {"name": "Theta", "justify": "right"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command()
def conditions(
    ticktype: str = typer.Argument("trade", help="Tick type: trade or quote"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get option condition codes."""
    client = AlpacaClient()
    data = client.get(f"/v1beta1/options/meta/conditions/{ticktype}", base=ApiBase.DATA)

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command()
def exchanges(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get option exchange codes."""
    client = AlpacaClient()
    data = client.get("/v1beta1/options/meta/exchanges", base=ApiBase.DATA)

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)
