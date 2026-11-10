import io
import time
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from sqlalchemy import func

from config import CALENDAR_DAYS_OF_HISTORY
from db_models import Price

URL = "https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{}.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def download_day(day):
    """Prices of every stock for one day, or None on a holiday or when the file is not ready."""
    url = URL.format(day.strftime("%d%m%Y"))
    try:
        response = requests.get(url, headers=HEADERS, timeout=40)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None

    table = pd.read_csv(io.StringIO(response.text))
    table.columns = [column.strip() for column in table.columns]
    table = table[table["SERIES"].str.strip() == "EQ"]

    # on a holiday NSE gives an older day's file, so we check the date inside the file
    file_day = datetime.strptime(table["DATE1"].iloc[0].strip(), "%d-%b-%Y").date()
    if file_day != day:
        return None

    prices = pd.DataFrame({
        "symbol": table["SYMBOL"].str.strip(),
        "open": pd.to_numeric(table["OPEN_PRICE"], errors="coerce"),
        "high": pd.to_numeric(table["HIGH_PRICE"], errors="coerce"),
        "low": pd.to_numeric(table["LOW_PRICE"], errors="coerce"),
        "close": pd.to_numeric(table["CLOSE_PRICE"], errors="coerce"),
        "volume": pd.to_numeric(table["TTL_TRD_QNTY"], errors="coerce"),
    })
    return prices.dropna()


def save_day(db, day, prices):
    # remove the day first, so running twice never makes duplicate rows
    db.query(Price).filter(Price.date == day).delete()

    new_rows = []
    for row in prices.itertuples():
        new_rows.append(Price(date=day, symbol=row.symbol, open=row.open, high=row.high,
                              low=row.low, close=row.close, volume=row.volume))
    db.add_all(new_rows)
    db.commit()


def last_saved_day(db):
    return db.query(func.max(Price.date)).scalar()


def update_prices(db, today=None):
    """Downloads every day that is missing, up to today. Returns the list of days added."""
    today = today or date.today()
    last_day = last_saved_day(db)
    if last_day is None:
        day = today - timedelta(days=CALENDAR_DAYS_OF_HISTORY)
        print("First run: downloading about a year of prices. This takes a few minutes.")
    else:
        day = last_day + timedelta(days=1)

    added = []
    while day <= today:
        if day.weekday() < 5:                   # Monday to Friday only
            prices = download_day(day)
            if prices is not None:
                save_day(db, day, prices)
                added.append(day)
                print("saved", day, len(prices), "stocks")
            time.sleep(0.3)                     # be polite to the NSE website
        day = day + timedelta(days=1)
    return added


def latest_closes(db):
    """symbol -> close price on the last saved day."""
    last_day = last_saved_day(db)
    if last_day is None:
        return {}
    rows = db.query(Price.symbol, Price.close).filter(Price.date == last_day).all()
    closes = {}
    for row in rows:
        closes[row.symbol] = row.close
    return closes


def load_prices(db, calendar_days=CALENDAR_DAYS_OF_HISTORY):
    """All saved prices of the last `calendar_days` days, as a pandas table."""
    last_day = last_saved_day(db)
    if last_day is None:
        return pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])

    first_day = last_day - timedelta(days=calendar_days)
    query = db.query(Price.date, Price.symbol, Price.open, Price.high, Price.low, Price.close, Price.volume)
    query = query.filter(Price.date >= first_day)
    return pd.read_sql(query.statement, db.bind, parse_dates=["date"])
