"""News commands."""

from __future__ import annotations

from typing import Optional

import typer

from bot.cli.client import AlpacaClient, ApiBase
from bot.cli.formatting import console, output_json, make_table

app = typer.Typer(no_args_is_help=False, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def news(
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols filter"),
    start: Optional[str] = typer.Option(None, help="Start date (RFC3339)"),
    end: Optional[str] = typer.Option(None, help="End date (RFC3339)"),
    limit: int = typer.Option(10, help="Max articles"),
    sort: str = typer.Option("desc", help="asc or desc"),
    include_content: bool = typer.Option(False, "--content", help="Include full article content"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Get market news articles."""
    client = AlpacaClient()
    data = client.get(
        "/v1beta1/news",
        base=ApiBase.DATA,
        params={
            "symbols": symbols,
            "start": start,
            "end": end,
            "limit": limit,
            "sort": sort,
            "include_content": include_content,
        },
    )

    if json_output:
        output_json(data)
        return

    articles = data.get("news", [])
    if not articles:
        console.print("[dim]No news articles found[/dim]")
        return

    for a in articles:
        syms = ", ".join(a.get("symbols", []))
        console.print(f"\n[bold]{a.get('headline', 'No headline')}[/bold]")
        console.print(f"  Source: {a.get('source', '?')} | Symbols: {syms} | {str(a.get('created_at', ''))[:19]}")
        if a.get("summary"):
            console.print(f"  {a['summary'][:200]}...")
        if a.get("url"):
            console.print(f"  [dim]{a['url']}[/dim]")
    console.print()
