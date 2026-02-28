"""Stock market data commands: bars, quotes, trades, snapshots, auctions, meta."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, ApiBase
from bot.cli.formatting import console, output_json, make_table, format_money

app = typer.Typer(no_args_is_help=True)

DEFAULT_FEED = "iex"


@app.command()
def bars(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    timeframe: str = typer.Option("1Day", help="1Min, 5Min, 15Min, 1Hour, 1Day, 1Week, 1Month"),
    start: Optional[str] = typer.Option(None, help="Start date (YYYY-MM-DD or RFC3339)"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max bars"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    sort: str = typer.Option("desc", help="asc or desc"),
    adjustment: str = typer.Option("raw", help="raw, split, dividend, all"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical price bars for a symbol."""
    client = AlpacaClient()
    data = client.get(
        f"/v2/stocks/{symbol}/bars",
        base=ApiBase.DATA,
        params={
            "timeframe": timeframe, "start": start, "end": end,
            "limit": limit, "feed": feed, "sort": sort, "adjustment": adjustment,
        },
    )

    if json_output:
        output_json(data)
        return

    bars_list = data.get("bars", [])
    if not bars_list:
        console.print("[dim]No bars returned[/dim]")
        return

    rows = []
    for b in bars_list:
        rows.append((
            str(b.get("t", ""))[:19],
            format_money(b.get("o", 0)),
            format_money(b.get("h", 0)),
            format_money(b.get("l", 0)),
            format_money(b.get("c", 0)),
            f"{b.get('v', 0):,}",
            str(b.get("n", "")),
            format_money(b.get("vw", 0)),
        ))

    table = make_table(
        title=f"{symbol} Bars ({timeframe})",
        columns=[
            {"name": "Time"}, {"name": "Open", "justify": "right"},
            {"name": "High", "justify": "right"}, {"name": "Low", "justify": "right"},
            {"name": "Close", "justify": "right"}, {"name": "Volume", "justify": "right"},
            {"name": "Trades", "justify": "right"}, {"name": "VWAP", "justify": "right"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command("bars-multi")
def bars_multi(
    symbols: str = typer.Argument(..., help="Comma-separated symbols (e.g., AAPL,MSFT,TSLA)"),
    timeframe: str = typer.Option("1Day", help="1Min, 5Min, 15Min, 1Hour, 1Day, 1Week, 1Month"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(10, help="Max bars per symbol"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    sort: str = typer.Option("desc", help="asc or desc"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical bars for multiple symbols."""
    client = AlpacaClient()
    data = client.get(
        "/v2/stocks/bars",
        base=ApiBase.DATA,
        params={
            "symbols": symbols, "timeframe": timeframe, "start": start,
            "end": end, "limit": limit, "feed": feed, "sort": sort,
        },
    )

    if json_output:
        output_json(data)
        return

    bars_map = data.get("bars", {})
    for sym, bar_list in bars_map.items():
        rows = [(str(b.get("t", ""))[:19], format_money(b.get("o", 0)),
                 format_money(b.get("h", 0)), format_money(b.get("l", 0)),
                 format_money(b.get("c", 0)), f"{b.get('v', 0):,}")
                for b in bar_list]
        table = make_table(
            title=f"{sym} Bars",
            columns=[{"name": "Time"}, {"name": "Open", "justify": "right"},
                     {"name": "High", "justify": "right"}, {"name": "Low", "justify": "right"},
                     {"name": "Close", "justify": "right"}, {"name": "Volume", "justify": "right"}],
            rows=rows,
        )
        console.print(table)
        console.print()


@app.command("bars-latest")
def bars_latest(
    symbol: Optional[str] = typer.Argument(None, help="Symbol (omit for multi-symbol with --symbols)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get the latest bar(s)."""
    client = AlpacaClient()
    if symbol:
        data = client.get(f"/v2/stocks/{symbol}/bars/latest", base=ApiBase.DATA, params={"feed": feed})
    else:
        data = client.get("/v2/stocks/bars/latest", base=ApiBase.DATA,
                          params={"symbols": symbols, "feed": feed})

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command()
def quote(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get the latest quote for a symbol."""
    client = AlpacaClient()
    data = client.get(f"/v2/stocks/{symbol}/quotes/latest", base=ApiBase.DATA, params={"feed": feed})

    if json_output:
        output_json(data)
        return

    q = data.get("quote", data)
    bid = float(q.get("bp", 0))
    ask = float(q.get("ap", 0))
    mid = (bid + ask) / 2 if bid and ask else 0

    table = make_table(
        title=f"{symbol} Latest Quote",
        columns=[{"name": "Field"}, {"name": "Value", "justify": "right"}],
        rows=[
            ("Bid", f"{format_money(bid)} x {q.get('bs', '?')}"),
            ("Ask", f"{format_money(ask)} x {q.get('as', '?')}"),
            ("Mid", format_money(mid)),
            ("Bid Exchange", str(q.get("bx", ""))),
            ("Ask Exchange", str(q.get("ax", ""))),
            ("Timestamp", str(q.get("t", ""))[:26]),
        ],
    )
    console.print(table)


@app.command()
def quotes(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max quotes"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    sort: str = typer.Option("desc", help="asc or desc"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical quotes for a symbol."""
    client = AlpacaClient()
    data = client.get(
        f"/v2/stocks/{symbol}/quotes",
        base=ApiBase.DATA,
        params={"start": start, "end": end, "limit": limit, "feed": feed, "sort": sort},
    )

    if json_output:
        output_json(data)
        return

    quotes_list = data.get("quotes", [])
    if not quotes_list:
        console.print("[dim]No quotes returned[/dim]")
        return

    rows = [(str(q.get("t", ""))[:26], format_money(q.get("bp", 0)),
             str(q.get("bs", "")), format_money(q.get("ap", 0)),
             str(q.get("as", "")))
            for q in quotes_list]

    table = make_table(
        title=f"{symbol} Quotes",
        columns=[{"name": "Time"}, {"name": "Bid", "justify": "right"},
                 {"name": "Bid Sz", "justify": "right"}, {"name": "Ask", "justify": "right"},
                 {"name": "Ask Sz", "justify": "right"}],
        rows=rows,
    )
    console.print(table)


@app.command("quotes-multi")
def quotes_multi(
    symbols: str = typer.Argument(..., help="Comma-separated symbols"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(10, help="Max quotes per symbol"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical quotes for multiple symbols."""
    client = AlpacaClient()
    data = client.get(
        "/v2/stocks/quotes", base=ApiBase.DATA,
        params={"symbols": symbols, "start": start, "end": end, "limit": limit, "feed": feed},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("quotes-latest")
def quotes_latest(
    symbols: str = typer.Argument(..., help="Comma-separated symbols"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get latest quotes for multiple symbols."""
    client = AlpacaClient()
    data = client.get("/v2/stocks/quotes/latest", base=ApiBase.DATA,
                      params={"symbols": symbols, "feed": feed})

    if json_output:
        output_json(data)
        return

    quotes_map = data.get("quotes", {})
    rows = []
    for sym, q in quotes_map.items():
        rows.append((sym, format_money(q.get("bp", 0)), format_money(q.get("ap", 0)),
                      str(q.get("t", ""))[:19]))

    table = make_table(
        title="Latest Quotes",
        columns=[{"name": "Symbol"}, {"name": "Bid", "justify": "right"},
                 {"name": "Ask", "justify": "right"}, {"name": "Time"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def trades(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max trades"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    sort: str = typer.Option("desc", help="asc or desc"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical trades for a symbol."""
    client = AlpacaClient()
    data = client.get(
        f"/v2/stocks/{symbol}/trades",
        base=ApiBase.DATA,
        params={"start": start, "end": end, "limit": limit, "feed": feed, "sort": sort},
    )

    if json_output:
        output_json(data)
        return

    trades_list = data.get("trades", [])
    if not trades_list:
        console.print("[dim]No trades returned[/dim]")
        return

    rows = [(str(t.get("t", ""))[:26], format_money(t.get("p", 0)),
             str(t.get("s", "")), str(t.get("x", "")), str(t.get("i", "")))
            for t in trades_list]

    table = make_table(
        title=f"{symbol} Trades",
        columns=[{"name": "Time"}, {"name": "Price", "justify": "right"},
                 {"name": "Size", "justify": "right"}, {"name": "Exchange"},
                 {"name": "Trade ID"}],
        rows=rows,
    )
    console.print(table)


@app.command("trades-multi")
def trades_multi(
    symbols: str = typer.Argument(..., help="Comma-separated symbols"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(10, help="Max trades per symbol"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical trades for multiple symbols."""
    client = AlpacaClient()
    data = client.get(
        "/v2/stocks/trades", base=ApiBase.DATA,
        params={"symbols": symbols, "start": start, "end": end, "limit": limit, "feed": feed},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("trade-latest")
def trade_latest(
    symbol: Optional[str] = typer.Argument(None, help="Symbol (omit for multi with --symbols)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get the latest trade(s)."""
    client = AlpacaClient()
    if symbol:
        data = client.get(f"/v2/stocks/{symbol}/trades/latest", base=ApiBase.DATA, params={"feed": feed})
    else:
        data = client.get("/v2/stocks/trades/latest", base=ApiBase.DATA,
                          params={"symbols": symbols, "feed": feed})

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command()
def snapshot(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get a full snapshot for a symbol (quote + trade + bar)."""
    client = AlpacaClient()
    data = client.get(f"/v2/stocks/{symbol}/snapshot", base=ApiBase.DATA, params={"feed": feed})

    if json_output:
        output_json(data)
        return

    lt = data.get("latestTrade", data.get("latest_trade", {}))
    lq = data.get("latestQuote", data.get("latest_quote", {}))
    mb = data.get("minuteBar", data.get("minute_bar", {}))
    db = data.get("dailyBar", data.get("daily_bar", {}))
    pb = data.get("prevDailyBar", data.get("prev_daily_bar", {}))

    rows = [
        ("Latest Trade", f"{format_money(lt.get('p', 0))} x {lt.get('s', '?')}"),
        ("Latest Quote", f"Bid {format_money(lq.get('bp', 0))} / Ask {format_money(lq.get('ap', 0))}"),
        ("Minute Bar", f"O:{format_money(mb.get('o', 0))} H:{format_money(mb.get('h', 0))} "
                       f"L:{format_money(mb.get('l', 0))} C:{format_money(mb.get('c', 0))} V:{mb.get('v', 0):,}"),
        ("Daily Bar", f"O:{format_money(db.get('o', 0))} H:{format_money(db.get('h', 0))} "
                      f"L:{format_money(db.get('l', 0))} C:{format_money(db.get('c', 0))} V:{db.get('v', 0):,}"),
        ("Prev Daily Bar", f"O:{format_money(pb.get('o', 0))} H:{format_money(pb.get('h', 0))} "
                           f"L:{format_money(pb.get('l', 0))} C:{format_money(pb.get('c', 0))} V:{pb.get('v', 0):,}"),
    ]

    table = make_table(
        title=f"{symbol} Snapshot",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def snapshots(
    symbols: str = typer.Argument(..., help="Comma-separated symbols"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get snapshots for multiple symbols."""
    client = AlpacaClient()
    data = client.get("/v2/stocks/snapshots", base=ApiBase.DATA,
                      params={"symbols": symbols, "feed": feed})

    if json_output:
        output_json(data)
        return

    rows = []
    for sym, snap in data.items():
        lt = snap.get("latestTrade", snap.get("latest_trade", {}))
        lq = snap.get("latestQuote", snap.get("latest_quote", {}))
        db = snap.get("dailyBar", snap.get("daily_bar", {}))
        rows.append((
            sym,
            format_money(lt.get("p", 0)),
            format_money(lq.get("bp", 0)),
            format_money(lq.get("ap", 0)),
            format_money(db.get("o", 0)),
            format_money(db.get("h", 0)),
            format_money(db.get("l", 0)),
            f"{db.get('v', 0):,}",
        ))

    table = make_table(
        title="Snapshots",
        columns=[
            {"name": "Symbol"}, {"name": "Last", "justify": "right"},
            {"name": "Bid", "justify": "right"}, {"name": "Ask", "justify": "right"},
            {"name": "Open", "justify": "right"}, {"name": "High", "justify": "right"},
            {"name": "Low", "justify": "right"}, {"name": "Volume", "justify": "right"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command()
def auctions(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(20, help="Max results"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical auction data for a symbol."""
    client = AlpacaClient()
    data = client.get(
        f"/v2/stocks/{symbol}/auctions",
        base=ApiBase.DATA,
        params={"start": start, "end": end, "limit": limit, "feed": feed},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command("auctions-multi")
def auctions_multi(
    symbols: str = typer.Argument(..., help="Comma-separated symbols"),
    start: Optional[str] = typer.Option(None, help="Start date"),
    end: Optional[str] = typer.Option(None, help="End date"),
    limit: int = typer.Option(10, help="Max per symbol"),
    feed: str = typer.Option(DEFAULT_FEED, help="Data feed: iex, sip"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get historical auctions for multiple symbols."""
    client = AlpacaClient()
    data = client.get(
        "/v2/stocks/auctions", base=ApiBase.DATA,
        params={"symbols": symbols, "start": start, "end": end, "limit": limit, "feed": feed},
    )

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command()
def conditions(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get stock condition codes."""
    client = AlpacaClient()
    data = client.get("/v2/stocks/meta/conditions", base=ApiBase.DATA)

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)


@app.command()
def exchanges(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get stock exchange codes."""
    client = AlpacaClient()
    data = client.get("/v2/stocks/meta/exchanges", base=ApiBase.DATA)

    if json_output:
        output_json(data)
        return

    console.print_json(data=data)
