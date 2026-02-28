"""Order commands: create, list, get, replace, cancel."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import (
    console, output_json, make_table, format_money, format_status,
    error_msg, success_msg,
)

app = typer.Typer(no_args_is_help=True)


def _print_order(data: dict) -> None:
    """Pretty-print a single order."""
    rows = [
        ("Order ID", data.get("id", "")),
        ("Client Order ID", data.get("client_order_id", "")),
        ("Symbol", data.get("symbol", "")),
        ("Side", data.get("side", "").upper()),
        ("Type", data.get("type", "")),
        ("Qty", str(data.get("qty") or data.get("notional", ""))),
        ("Filled Qty", str(data.get("filled_qty", "0"))),
        ("Status", data.get("status", "")),
        ("Time in Force", data.get("time_in_force", "")),
        ("Order Class", data.get("order_class", "simple")),
    ]
    if data.get("limit_price"):
        rows.append(("Limit Price", format_money(data["limit_price"])))
    if data.get("stop_price"):
        rows.append(("Stop Price", format_money(data["stop_price"])))
    if data.get("trail_price"):
        rows.append(("Trail Price", format_money(data["trail_price"])))
    if data.get("trail_percent"):
        rows.append(("Trail Percent", f"{data['trail_percent']}%"))
    if data.get("filled_avg_price"):
        rows.append(("Fill Price", format_money(data["filled_avg_price"])))
    if data.get("extended_hours"):
        rows.append(("Extended Hours", "Yes"))
    rows.append(("Submitted", str(data.get("submitted_at", ""))[:19]))
    if data.get("filled_at"):
        rows.append(("Filled", str(data["filled_at"])[:19]))
    if data.get("legs"):
        for i, leg in enumerate(data["legs"]):
            rows.append((f"Leg {i+1}", f"{leg.get('side', '').upper()} {leg.get('type', '')} "
                        f"qty={leg.get('qty', '')} status={leg.get('status', '')}"))

    table = make_table(
        title="Order Detail",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def create(
    symbol: str = typer.Argument(..., help="Ticker symbol (e.g., AAPL)"),
    side: str = typer.Argument(..., help="buy or sell"),
    qty: Optional[float] = typer.Option(None, help="Number of shares"),
    notional: Optional[float] = typer.Option(None, help="Dollar amount (fractional shares)"),
    order_type: str = typer.Option("market", "--type", help="market, limit, stop, stop_limit, trailing_stop"),
    time_in_force: str = typer.Option("day", "--tif", help="day, gtc, ioc, fok, opg, cls"),
    limit_price: Optional[float] = typer.Option(None, "--limit-price", help="Limit price"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", help="Stop price"),
    trail_price: Optional[float] = typer.Option(None, help="Trail amount in dollars"),
    trail_percent: Optional[float] = typer.Option(None, help="Trail percentage"),
    extended_hours: bool = typer.Option(False, help="Allow extended hours"),
    order_class: Optional[str] = typer.Option(None, "--class", help="simple, bracket, oco, oto"),
    take_profit_price: Optional[float] = typer.Option(None, "--tp", help="Take-profit limit price"),
    stop_loss_price: Optional[float] = typer.Option(None, "--sl", help="Stop-loss stop price"),
    stop_loss_limit: Optional[float] = typer.Option(None, "--sl-limit", help="Stop-loss limit price"),
    client_order_id: Optional[str] = typer.Option(None, "--client-id", help="Custom client order ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Create a new order (market, limit, stop, bracket, OCO, OTO)."""
    if qty is None and notional is None:
        error_msg("Must provide either --qty or --notional")
        raise typer.Exit(1)

    body: dict = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force,
    }

    if qty is not None:
        body["qty"] = str(qty)
    if notional is not None:
        body["notional"] = str(notional)
    if limit_price is not None:
        body["limit_price"] = str(limit_price)
    if stop_price is not None:
        body["stop_price"] = str(stop_price)
    if trail_price is not None:
        body["trail_price"] = str(trail_price)
    if trail_percent is not None:
        body["trail_percent"] = str(trail_percent)
    if extended_hours:
        body["extended_hours"] = True
    if client_order_id:
        body["client_order_id"] = client_order_id
    if order_class:
        body["order_class"] = order_class
    if take_profit_price is not None:
        body["take_profit"] = {"limit_price": str(take_profit_price)}
    if stop_loss_price is not None:
        sl: dict = {"stop_price": str(stop_loss_price)}
        if stop_loss_limit is not None:
            sl["limit_price"] = str(stop_loss_limit)
        body["stop_loss"] = sl

    client = AlpacaClient()
    data = client.post("/v2/orders", json=body)

    if json_output:
        output_json(data)
        return

    success_msg("Order created")
    _print_order(data)


@app.command("list")
def list_orders(
    status: str = typer.Option("open", help="open, closed, all"),
    limit: int = typer.Option(50, help="Max results"),
    after: Optional[str] = typer.Option(None, help="After timestamp (RFC3339)"),
    until: Optional[str] = typer.Option(None, help="Until timestamp (RFC3339)"),
    direction: str = typer.Option("desc", help="asc or desc"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols filter"),
    side: Optional[str] = typer.Option(None, help="Filter by side: buy or sell"),
    nested: bool = typer.Option(True, help="Include nested legs for multi-leg orders"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List orders (default: open)."""
    client = AlpacaClient()
    data = client.get(
        "/v2/orders",
        params={
            "status": status,
            "limit": limit,
            "after": after,
            "until": until,
            "direction": direction,
            "symbols": symbols,
            "side": side,
            "nested": nested,
        },
    )

    if json_output:
        output_json(data)
        return

    if not data:
        console.print(f"[dim]No {status} orders[/dim]")
        return

    rows = []
    for o in data:
        rows.append((
            o.get("id", "")[:8] + "...",
            o.get("symbol", ""),
            o.get("side", "").upper(),
            o.get("type", ""),
            str(o.get("qty") or o.get("notional", "?")),
            format_money(o["limit_price"]) if o.get("limit_price") else "-",
            format_status(o.get("status", "")),
            str(o.get("filled_qty", "0")),
            str(o.get("submitted_at", ""))[:19],
        ))

    table = make_table(
        title=f"Orders ({status})",
        columns=[
            {"name": "ID"}, {"name": "Symbol"}, {"name": "Side"},
            {"name": "Type"}, {"name": "Qty", "justify": "right"},
            {"name": "Limit", "justify": "right"}, {"name": "Status"},
            {"name": "Filled", "justify": "right"}, {"name": "Submitted"},
        ],
        rows=rows,
    )
    console.print(table)


@app.command()
def get(
    order_id: str = typer.Argument(..., help="Order ID"),
    nested: bool = typer.Option(True, help="Include nested legs"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get order by ID."""
    client = AlpacaClient()
    data = client.get(f"/v2/orders/{order_id}", params={"nested": nested})

    if json_output:
        output_json(data)
        return

    _print_order(data)


@app.command("get-by-client-id")
def get_by_client_id(
    client_order_id: str = typer.Argument(..., help="Client order ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get order by client order ID."""
    client = AlpacaClient()
    data = client.get("/v2/orders:by_client_order_id", params={"client_order_id": client_order_id})

    if json_output:
        output_json(data)
        return

    _print_order(data)


@app.command()
def replace(
    order_id: str = typer.Argument(..., help="Order ID to replace"),
    qty: Optional[float] = typer.Option(None, help="New quantity"),
    limit_price: Optional[float] = typer.Option(None, "--limit-price", help="New limit price"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", help="New stop price"),
    trail: Optional[float] = typer.Option(None, help="New trail amount"),
    time_in_force: Optional[str] = typer.Option(None, "--tif", help="New time in force"),
    client_order_id: Optional[str] = typer.Option(None, "--client-id", help="New client order ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Replace (modify) an existing order."""
    body: dict = {}
    if qty is not None:
        body["qty"] = str(qty)
    if limit_price is not None:
        body["limit_price"] = str(limit_price)
    if stop_price is not None:
        body["stop_price"] = str(stop_price)
    if trail is not None:
        body["trail"] = str(trail)
    if time_in_force is not None:
        body["time_in_force"] = time_in_force
    if client_order_id is not None:
        body["client_order_id"] = client_order_id

    if not body:
        error_msg("No replacement fields provided. Use --help to see options.")
        raise typer.Exit(1)

    client = AlpacaClient()
    data = client.patch(f"/v2/orders/{order_id}", json=body)

    if json_output:
        output_json(data)
        return

    success_msg("Order replaced")
    _print_order(data)


@app.command()
def cancel(
    order_id: str = typer.Argument(..., help="Order ID to cancel"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Cancel an order by ID."""
    client = AlpacaClient()
    data = client.delete(f"/v2/orders/{order_id}")

    if json_output:
        output_json(data or {"status": "canceled"})
        return

    success_msg(f"Order {order_id} canceled")


@app.command("cancel-all")
def cancel_all(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Cancel all open orders."""
    client = AlpacaClient()
    data = client.delete("/v2/orders")

    if json_output:
        output_json(data or [])
        return

    if data:
        console.print(f"[bold green]Canceled {len(data)} order(s)[/bold green]")
        for o in data:
            body = o.get("body", o)
            console.print(f"  {body.get('id', '?')[:8]}... {body.get('symbol', '')} {body.get('side', '')}")
    else:
        console.print("[dim]No open orders to cancel[/dim]")
