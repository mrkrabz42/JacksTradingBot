"""Crypto funding commands: wallets, transfers, whitelisted addresses, fee estimates."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient
from bot.cli.formatting import (
    console, output_json, make_table, format_money, error_msg, success_msg,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def wallets(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List crypto wallets."""
    client = AlpacaClient()
    data = client.get("/v2/wallets")

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No crypto wallets[/dim]")
        return

    rows = []
    for w in data:
        rows.append((
            w.get("id", "")[:8] + "...",
            w.get("asset", ""),
            str(w.get("balance", "")),
            str(w.get("available_balance", "")),
            str(w.get("status", "")),
        ))

    table = make_table(
        title="Crypto Wallets",
        columns=[{"name": "ID"}, {"name": "Asset"}, {"name": "Balance", "justify": "right"},
                 {"name": "Available", "justify": "right"}, {"name": "Status"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def transfers(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List crypto transfers."""
    client = AlpacaClient()
    data = client.get("/v2/wallets/transfers")

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No transfers[/dim]")
        return

    rows = []
    for t in data:
        rows.append((
            t.get("id", "")[:8] + "...",
            t.get("asset", ""),
            t.get("direction", ""),
            str(t.get("amount", "")),
            t.get("status", ""),
            str(t.get("created_at", ""))[:19],
        ))

    table = make_table(
        title="Crypto Transfers",
        columns=[{"name": "ID"}, {"name": "Asset"}, {"name": "Direction"},
                 {"name": "Amount", "justify": "right"}, {"name": "Status"}, {"name": "Created"}],
        rows=rows,
    )
    console.print(table)


@app.command("transfer-create")
def transfer_create(
    amount: str = typer.Argument(..., help="Amount to transfer"),
    asset: str = typer.Argument(..., help="Crypto asset (e.g., BTC, ETH)"),
    address: str = typer.Option(..., help="Destination address"),
    network: Optional[str] = typer.Option(None, help="Network (e.g., ethereum, bitcoin)"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Create a crypto withdrawal."""
    body: dict = {
        "amount": amount,
        "asset": asset,
        "address": address,
    }
    if network:
        body["network"] = network

    client = AlpacaClient()
    data = client.post("/v2/wallets/transfers", json=body)

    if json_output:
        output_json(data)
        return

    success_msg("Transfer created")
    console.print_json(data=data)


@app.command("transfer")
def get_transfer(
    transfer_id: str = typer.Argument(..., help="Transfer ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get a specific transfer."""
    client = AlpacaClient()
    data = client.get(f"/v2/wallets/transfers/{transfer_id}")

    if json_output:
        output_json(data)
        return

    rows = [(k, str(v)) for k, v in data.items()]
    table = make_table(
        title=f"Transfer: {transfer_id}",
        columns=[{"name": "Field"}, {"name": "Value"}],
        rows=rows,
    )
    console.print(table)


@app.command()
def addresses(
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """List whitelisted crypto addresses."""
    client = AlpacaClient()
    data = client.get("/v2/wallets/whitelisted_addresses")

    if json_output:
        output_json(data)
        return

    if not data:
        console.print("[dim]No whitelisted addresses[/dim]")
        return

    rows = []
    for a in data:
        rows.append((
            a.get("id", "")[:8] + "...",
            a.get("asset", ""),
            a.get("address", "")[:30] + "...",
            a.get("network", ""),
            a.get("status", ""),
        ))

    table = make_table(
        title="Whitelisted Addresses",
        columns=[{"name": "ID"}, {"name": "Asset"}, {"name": "Address"},
                 {"name": "Network"}, {"name": "Status"}],
        rows=rows,
    )
    console.print(table)


@app.command("address-create")
def address_create(
    address: str = typer.Argument(..., help="Crypto address"),
    asset: str = typer.Argument(..., help="Asset (e.g., BTC, ETH)"),
    network: Optional[str] = typer.Option(None, help="Network"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Whitelist a new crypto address."""
    body: dict = {"address": address, "asset": asset}
    if network:
        body["network"] = network

    client = AlpacaClient()
    data = client.post("/v2/wallets/whitelisted_addresses", json=body)

    if json_output:
        output_json(data)
        return

    success_msg("Address whitelisted")
    console.print_json(data=data)


@app.command("address-delete")
def address_delete(
    address_id: str = typer.Argument(..., help="Whitelisted address ID"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Remove a whitelisted crypto address."""
    client = AlpacaClient()
    client.delete(f"/v2/wallets/whitelisted_addresses/{address_id}")

    if json_output:
        output_json({"status": "deleted", "id": address_id})
        return

    success_msg(f"Address {address_id} removed")


@app.command("fee-estimate")
def fee_estimate(
    asset: str = typer.Argument(..., help="Crypto asset (e.g., BTC, ETH)"),
    from_address: Optional[str] = typer.Option(None, "--from", help="From address"),
    to_address: Optional[str] = typer.Option(None, "--to", help="To address"),
    amount: Optional[str] = typer.Option(None, help="Amount"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get gas fee estimate for crypto transfer."""
    client = AlpacaClient()
    data = client.get(
        "/v2/wallets/fees/estimate",
        params={
            "asset": asset,
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
        },
    )

    if json_output:
        output_json(data)
        return

    rows = [(k, str(v)) for k, v in data.items()]
    table = make_table(
        title=f"Fee Estimate: {asset}",
        columns=[{"name": "Field"}, {"name": "Value", "justify": "right"}],
        rows=rows,
    )
    console.print(table)
