# Road to 10K v2 — Market Analysis Assistant

An eagle-eyed market analysis assistant that identifies high-probability setups, regime shifts, and liquidity draws to help human traders make better decisions.

**This is NOT an automated trading bot** — it analyzes, you decide.

## What It Does

- Scans watchlist for SMA crossover signals every 5 minutes
- Runs a 13-engine analysis pipeline on each signal:
  - Market structure shifts (MSS) + displacement + acceptance
  - Regime detection (trending/ranging/volatile)
  - Volatility state + ATR analysis
  - Trend direction + strength scoring
  - Volume profile + participation analysis
  - Liquidity draw mapping + session levels
  - Multi-timeframe alignment
  - Confluence scoring + context grading
- Reports setup grades, bias, and environment summaries
- Dashboard for visual analysis review

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
cd dashboard && npm install
```

2. Copy `.env.example` to `.env` and add your Alpaca API keys:
```bash
cp .env.example .env
```

3. Run the analyzer:
```bash
python bot/main.py
```

4. Start the dashboard:
```bash
cd dashboard && npm run dev
```

## Project Structure

- `bot/` — Analysis engine (13 pipeline modules, signal generation, risk analysis)
- `backtest/` — Backtesting module with candlestick visualization
- `dashboard/` — Next.js analysis dashboard
- `tests/` — Unit tests for pipeline engines

## Status

**v2** — Market Analysis Assistant (execution disabled, analysis-only mode)
