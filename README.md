# Systematic Investing Platform

A rule based investing bot for NSE stocks. It runs a paper account, shows live prices from Fyers,
sends Telegram alerts and has a React dashboard.

## Strategy

- Every second Friday, rank NSE stocks (Rs 20 crore+ traded a day, price above Rs 20) by their 6 month return
- Only stocks in an uptrend: above the 50 day average and within 25% of the 1 year high
- Hold the top 5, keep a stock while it stays in the top 10
- If less than 40% of big stocks are above their 200 day average, sell everything and wait in cash
- Orders are planned in the evening and filled at the next day's open

## Features

- Daily NSE price download, runs by itself every weekday evening
- Paper trading with profits reinvested
- Fyers login, live prices and live P&L
- Live orders through Fyers (off by default, needs LIVE_TRADING_ENABLED=true and typing CONFIRM)
- Telegram alerts
- Performance chart against Nifty 50

## Tech

Python, FastAPI, SQLAlchemy, pandas, Fyers API, React, Docker

## Run

Backend:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Frontend:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and log in with the admin user from .env.

Tests: `cd backend` then `pytest`
