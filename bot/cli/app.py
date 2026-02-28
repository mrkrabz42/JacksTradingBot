"""Root Typer app — registers all command groups."""

from __future__ import annotations

import typer

from bot.cli.client import AlpacaError
from bot.cli.formatting import error_msg

app = typer.Typer(
    name="alpaca",
    help="Alpaca Trading & Market Data CLI — complete API access.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _register_commands() -> None:
    """Import and register all command groups."""
    from bot.cli.commands import (
        account, orders, positions, assets, watchlists,
        calendar, corporate, crypto_fund,
        stocks, crypto_data, options_data, news, screener, other,
        sessions,
    )

    # Trading API
    app.add_typer(account.app, name="account", help="Account info, history, config, activities")
    app.add_typer(orders.app, name="orders", help="Create, list, cancel, replace orders")
    app.add_typer(positions.app, name="positions", help="View and manage positions")
    app.add_typer(assets.app, name="assets", help="Browse tradable assets and option contracts")
    app.add_typer(watchlists.app, name="watchlists", help="Manage watchlists")
    app.add_typer(corporate.app, name="corporate", help="Corporate action announcements")
    app.add_typer(crypto_fund.app, name="crypto-fund", help="Crypto wallets, transfers, addresses")

    # Market Data
    app.add_typer(stocks.app, name="stocks", help="Stock data: bars, quotes, trades, snapshots")
    app.add_typer(crypto_data.app, name="crypto", help="Crypto data: bars, quotes, trades, orderbook")
    app.add_typer(options_data.app, name="options", help="Options data: bars, quotes, chain, greeks")
    app.add_typer(news.app, name="news", help="Market news articles")
    app.add_typer(screener.app, name="screener", help="Stock screener: most-actives, movers")

    # Calendar (market clock and calendar)
    app.add_typer(calendar.app, name="market", help="Market clock and calendar")

    # Bonsai Session Liquidity
    app.add_typer(sessions.app, name="sessions", help="Session levels: highs, lows, PDH/PDL")

    # Misc (logos, forex, corporate-actions-data)
    other.register(app)


_register_commands()
