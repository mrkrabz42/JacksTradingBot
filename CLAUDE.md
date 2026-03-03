# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Road to 10K v2 is a **market analysis assistant** for human traders. It identifies market conditions, confluence setups, regime shifts, and liquidity draws to ASSIST (not automate) trading decisions. All 13 analysis pipeline engines are preserved — trade execution is disabled.

## Tech Stack
- **Analysis Engine**: Python 3.12+ with alpaca-py SDK (market data only)
- **Indicators**: ta (technical analysis) library
- **Backtesting**: backtesting.py library
- **Dashboard**: Next.js 14+ with Tailwind CSS and shadcn/ui
- **Scheduling**: schedule library for market-hours loop
- **Logging**: loguru
- **MCP**: Alpaca MCP Server for direct broker data access from Claude Code

## Commands
- Start analyzer: `python bot/main.py`
- Run backtest: `python backtest/run_backtest.py`
- Install dependencies: `pip install -r requirements.txt`
- Start dashboard: `cd dashboard && npm run dev`
- Run tests: `pytest tests/`

## Architecture
```
bot/main.py          → Entry point, runs analysis loop every 5 min during market hours
bot/config.py        → Loads .env, exposes all config constants
bot/data/            → Alpaca SDK wrappers for quotes, bars, account info
bot/pipeline/        → Enriched snapshot pipeline (13 analysis engines)
bot/strategies/      → Signal generation (BUY/SELL/HOLD)
bot/scanner/         → Scans watchlist, aggregates signals
bot/risk/            → Risk analysis (position sizing, stop-loss calc)
bot/execution/       → DISABLED — stubbed, logs warnings only
bot/structure/       → MSS detection, regime, order flow, sweep detection
bot/confluence/      → Confluence engine
bot/trend/           → Trend engine
bot/volatility/      → Volatility engine
bot/volume/          → Volume + participation engines
bot/liquidity/       → Liquidity draw + session levels
bot/mtf/             → Multi-timeframe alignment
bot/sessions/        → Session classification + extremes
bot/context/         → Context formatter (environment summary, flags, grades)
bot/snapshots/       → Market snapshot builder
bot/storage/         → Market data storage
backtest/            → Backtests strategies on historical data
dashboard/           → Next.js analysis dashboard
```

### Dashboard — Fundamentals & News Integration
```
dashboard/lib/fred.ts                → FRED API client (10 macro series, in-memory cache)
dashboard/lib/fundamentals-engine.ts → 7-factor scoring engine with asset-specific weights
dashboard/lib/economic-calendar.ts   → Static calendar of US/UK high-impact events
dashboard/app/api/fundamentals/      → GET /api/fundamentals?symbol= — scored macro data
dashboard/app/api/news/calendar/     → GET /api/news/calendar — upcoming economic events
dashboard/components/cards/fundamentals-panel.tsx → Expandable panel on pathway cards
dashboard/components/cards/news-board.tsx         → Economic calendar in right panel
dashboard/lib/hooks/use-fundamentals.ts  → SWR hook (5-min refresh)
dashboard/lib/hooks/use-news-calendar.ts → SWR hook (1-min refresh)
dashboard/lib/hooks/use-news-alerts.ts   → Toast alerts for imminent events
```
- **FRED API** (free): Interest rates, yields, CPI, PCE, employment, VIX, PMI
- **DXY proxy**: Inverse EUR/USD mid price from OANDA
- **Env vars**: `FRED_API_KEY` (required for fundamentals)

## IMPORTANT: Execution Disabled
- `bot/execution/executor.py` contains **stubs only** — no orders are placed
- The analysis pipeline runs fully but results are for human review only
- Do NOT re-enable execution without explicit user approval

## Coding Standards
- Python type hints on all function signatures
- async/await for all Alpaca API calls
- loguru for logging (not print)
- Wrap API calls in try/except with meaningful errors
- Environment variables via python-dotenv, never hardcode secrets

## Commit Convention
`type(scope): description` — types: feat, fix, refactor, docs, test, chore
