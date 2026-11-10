from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user
from broker import PaperBroker
from daily_job import run_daily_job
from database import get_db
from db_models import AccountDay, Order, PendingOrder, Price, Trade
from fyers_client import live_prices
from live_broker import place_pending_orders
from nse_data import latest_closes, load_prices
from strategy import latest_numbers, make_tables, rank_stocks

# every route in this file needs a logged in user
router = APIRouter(tags=["portfolio"], dependencies=[Depends(get_current_user)])


def market_is_open():
    """NSE is open 9:15 am to 3:30 pm, Monday to Friday (holidays are not checked)."""
    now = datetime.now()
    minutes = now.hour * 60 + now.minute
    return now.weekday() < 5 and 9 * 60 + 15 <= minutes <= 15 * 60 + 30


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    broker = PaperBroker(db)
    account = broker.account()
    total = broker.total_value(latest_closes(db))
    last_day = db.query(AccountDay).order_by(AccountDay.date.desc()).first()

    return {
        "start_cash": account.start_cash,
        "cash": round(account.cash, 2),
        "total_value": round(total, 2),
        "profit_percent": round((total / account.start_cash - 1) * 100, 2),
        "last_run": str(last_day.date) if last_day else None,
        "market_health": last_day.market_health if last_day else None,
        "market_open": market_is_open(),
    }


@router.get("/positions")
def positions(live: bool = False, db: Session = Depends(get_db)):
    """Our stocks with their profit. live=true uses live Fyers prices when we are logged in."""
    closes = latest_closes(db)
    held = PaperBroker(db).positions()

    live_now = {}
    if live:
        live_now = live_prices([position.symbol for position in held])

    result = []
    for position in held:
        price = live_now.get(position.symbol, closes.get(position.symbol, position.buy_price))
        profit = (price - position.buy_price) * position.shares
        result.append({
            "symbol": position.symbol,
            "shares": position.shares,
            "buy_date": str(position.buy_date),
            "buy_price": position.buy_price,
            "price": price,
            "is_live_price": position.symbol in live_now,
            "profit": round(profit, 2),
            "profit_percent": round((price / position.buy_price - 1) * 100, 2),
        })
    return result


@router.get("/orders")
def orders(db: Session = Depends(get_db)):
    rows = db.query(Order).order_by(Order.date.desc()).limit(100).all()
    waiting = db.query(PendingOrder).all()

    done = []
    for order in rows:
        done.append({"date": str(order.date), "symbol": order.symbol, "side": order.side,
                     "shares": order.shares, "price": order.price, "reason": order.reason})
    planned = []
    for order in waiting:
        planned.append({"symbol": order.symbol, "side": order.side, "reason": order.reason})
    return {"done": done, "waiting_for_tomorrow": planned}


@router.get("/trades")
def trades(db: Session = Depends(get_db)):
    rows = db.query(Trade).order_by(Trade.sell_date.desc()).all()
    result = []
    for trade in rows:
        result.append({"symbol": trade.symbol, "buy_date": str(trade.buy_date), "sell_date": str(trade.sell_date),
                       "buy_price": trade.buy_price, "sell_price": trade.sell_price,
                       "profit": round(trade.profit, 2)})
    return result


@router.get("/performance")
def performance(db: Session = Depends(get_db)):
    """Our account value next to Nifty (the NIFTYBEES ETF), both starting at the same amount, and the return of each month."""
    days = db.query(AccountDay).order_by(AccountDay.date).all()
    if len(days) == 0:
        return {"chart": [], "months": []}

    nifty_rows = db.query(Price.date, Price.close).filter(Price.symbol == "NIFTYBEES").all()
    nifty_by_day = {}
    for row in nifty_rows:
        nifty_by_day[row.date] = row.close

    start_value = days[0].total
    first_nifty = nifty_by_day.get(days[0].date)

    chart = []
    for day in days:
        point = {"date": str(day.date), "account": round(day.total, 2), "nifty": None}
        if first_nifty and day.date in nifty_by_day:
            point["nifty"] = round(start_value * nifty_by_day[day.date] / first_nifty, 2)
        chart.append(point)

    # the return of each month: last value of the month against the last value of the month before
    month_end = {}
    for day in days:
        month_end[day.date.strftime("%Y-%m")] = day.total

    months = []
    previous = start_value
    for month, value in month_end.items():
        months.append({"month": month, "return_percent": round((value / previous - 1) * 100, 2)})
        previous = value
    return {"chart": chart, "months": months}


@router.get("/signals")
def signals(db: Session = Depends(get_db)):
    """Today's top 10 stocks by the strategy's ranking."""
    prices = load_prices(db)
    if prices.empty:
        return []
    close, volume = make_tables(prices)
    ranked = rank_stocks(latest_numbers(close, volume))

    result = []
    rank = 1
    for symbol, value in ranked.head(10).items():
        result.append({"rank": rank, "symbol": symbol, "return_6_months_percent": round(value * 100, 1)})
        rank = rank + 1
    return result


@router.post("/run-daily-job")
def run_job(db: Session = Depends(get_db)):
    """Runs the evening job now. The first run downloads about a year of prices (a few minutes)."""
    return run_daily_job(db)


class LiveOrderRequest(BaseModel):
    confirm: str


@router.post("/live/place-orders")
def place_live_orders(request: LiveOrderRequest, db: Session = Depends(get_db)):
    """Sends the planned orders to Fyers as REAL orders. You must type CONFIRM."""
    if request.confirm != "CONFIRM":
        return {"results": ["Not sent. Type CONFIRM to send real orders."]}
    return {"results": place_pending_orders(db)}
