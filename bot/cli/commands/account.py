"""Account commands: info, portfolio history, configuration, activities."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, AlpacaError
from bot.cli.formatting import (
    console, output_json, make_table, format_money, format_pnl, format_pct,
    error_msg,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def info(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Show account details: equity, buying power, cash, P&L."""
    client = AlpacaClient()
    data = client.get("/v2/account")

    if json_output:
        output_json(data)
        return

    equity = float(data.get("equity", 0))
    last_equity = float(data.get("last_equity", 0))
    daily_pnl = equity - last_equity

    table = make_table(
        title="Account Summary",
        columns=[
            {"name": "Field"},
            {"name": "Value", "justify": "right"},
        ],
        rows=[
            ("Account #", data.get("account_number", "")),
            ("Status", data.get("status", "")),
            ("Equity", format_money(equity)),
            ("Cash", format_money(data.get("cash", 0))),
            ("Buying Power", format_money(data.get("buying_power", 0))),
            ("Portfolio Value", format_money(data.get("portfolio_value", 0))),
            ("Daily P&L", format_pnl(daily_pnl)),
            ("Long Market Value", format_money(data.get("long_market_value", 0))),
            ("Short Market Value", format_money(data.get("short_market_value", 0))),
            ("Pattern Day Trader", str(data.get("pattern_day_trader", False))),
            ("Trading Blocked", str(data.get("trading_blocked", False))),
            ("Shorting Enabled", str(data.get("shorting_enabled", False))),
            ("Multiplier", data.get("multiplier", "")),
        ],
    )
    console.print(table)


@app.command()
def history(
    period: str = typer.Option("1M", help="Period: 1D, 1W, 1M, 3M, 1A"),
    timeframe: str = typer.Option("1D", help="Timeframe: 1Min, 5Min, 15Min, 1H, 1D"),
    extended_hours: bool = typer.Option(False, help="Include extended hours"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Show portfolio value history."""
    client = AlpacaClient()
    data = client.get(
        "/v2/account/portfolio/history",
        params={
            "period": period,
            "timeframe": timeframe,
            "extended_hours": extended_hours,
        },
    )

    if json_output:
        output_json(data)
        return

    timestamps = data.get("timestamp", [])
    equity_values = data.get("equity", [])
    pnl_values = data.get("profit_loss", [])

    if not timestamps:
        console.print("[dim]No history data available[/dim]")
        return

    from datetime import datetime

    rows = []
    for ts, eq, pl in zip(timestamps[-20:], equity_values[-20:], pnl_values[-20:]):
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        rows.append((dt, format_money(eq), format_pnl(pl)))

    table = make_table(
        title=f"Portfolio History (last {len(rows)} of {len(timestamps)} points)",
        columns=[
            {"name": "Time"},
            {"name": "Equity", "justify": "right"},
            {"name": "P&L", "justify": "right"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command("config-get")
def config_get(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get account configurations."""
    client = AlpacaClient()
    data = client.get("/v2/account/configurations")

    if json_output:
        output_json(data)
        return

    rows = [(k, str(v)) for k, v in data.items()]
    table = make_table(
        title="Account Configurations",
        columns=[{"name": "Setting"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)


@app.command("config-update")
def config_update(
    dtbp_check: Optional[str] = typer.Option(None, help="Day trading buying power check: both, entry, exit"),
    no_shorting: Optional[bool] = typer.Option(None, help="Disable shorting"),
    trade_confirm_email: Optional[str] = typer.Option(None, help="Trade confirm email: all, none"),
    suspend_trade: Optional[bool] = typer.Option(None, help="Suspend trading"),
    fractional_trading: Optional[bool] = typer.Option(None, help="Enable fractional trading"),
    max_margin_multiplier: Optional[str] = typer.Option(None, help="Max margin multiplier: 1 or 2"),
    pdt_check: Optional[str] = typer.Option(None, help="PDT check: both, entry, exit"),
    ptp_no_exception_entry: Optional[bool] = typer.Option(None, help="PTP no exception on entry"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Update account configurations."""
    body = {}
    if dtbp_check is not None:
        body["dtbp_check"] = dtbp_check
    if no_shorting is not None:
        body["no_shorting"] = no_shorting
    if trade_confirm_email is not None:
        body["trade_confirm_email"] = trade_confirm_email
    if suspend_trade is not None:
        body["suspend_trade"] = suspend_trade
    if fractional_trading is not None:
        body["fractional_trading"] = fractional_trading
    if max_margin_multiplier is not None:
        body["max_margin_multiplier"] = max_margin_multiplier
    if pdt_check is not None:
        body["pdt_check"] = pdt_check
    if ptp_no_exception_entry is not None:
        body["ptp_no_exception_entry"] = ptp_no_exception_entry

    if not body:
        error_msg("No configuration options provided. Use --help to see options.")
        raise typer.Exit(1)

    client = AlpacaClient()
    data = client.patch("/v2/account/configurations", json=body)

    if json_output:
        output_json(data)
        return

    rows = [(k, str(v)) for k, v in data.items()]
    table = make_table(
        title="Updated Account Configurations",
        columns=[{"name": "Setting"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def activities(
    activity_type: Optional[str] = typer.Option(None, "--type", help="Filter by type (e.g., FILL, DIV, ACATC)"),
    after: Optional[str] = typer.Option(None, help="After timestamp (RFC3339)"),
    until: Optional[str] = typer.Option(None, help="Until timestamp (RFC3339)"),
    direction: str = typer.Option("desc", help="asc or desc"),
    page_size: int = typer.Option(50, help="Results per page"),
    page_token: Optional[str] = typer.Option(None, help="Pagination token"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List account activities (trades, dividends, transfers, etc.)."""
    client = AlpacaClient()
    path = f"/v2/account/activities/{activity_type}" if activity_type else "/v2/account/activities"
    data = client.get(
        path,
        params={
            "after": after,
            "until": until,
            "direction": direction,
            "page_size": page_size,
            "page_token": page_token,
        },
    )

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No activities found[/dim]")
        return

    rows = []
    for a in data:
        rows.append((
            a.get("id", "")[:12],
            a.get("activity_type", ""),
            a.get("symbol", "-"),
            a.get("side", "-"),
            str(a.get("qty", a.get("net_amount", "-"))),
            format_money(a.get("price", a.get("per_share_amount", 0))),
            str(a.get("transaction_time", a.get("date", "")))[:19],
        ))

    table = make_table(
        title="Account Activities",
        columns=[
            {"name": "ID"}, {"name": "Type"}, {"name": "Symbol"},
            {"name": "Side"}, {"name": "Qty", "justify": "right"},
            {"name": "Price", "justify": "right"}, {"name": "Time"},
        ],
        rows=rows,
    )
    console.print(table)
