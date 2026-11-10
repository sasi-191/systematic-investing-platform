from alerts import send_telegram
from broker import PaperBroker
from config import STOCKS_TO_HOLD
from database import Base, SessionLocal, engine
from db_models import AccountDay, PendingOrder
from nse_data import load_prices, update_prices
from strategy import (choose_trades, is_rebalance_day, latest_numbers, make_tables, market_health,
                      market_is_healthy, rank_stocks)


def fill_pending_orders(db, broker, day, open_prices):
    """Sells first, so the money is free for the buys. Returns a list of what was done."""
    pending = db.query(PendingOrder).filter(PendingOrder.decided_on < day).all()
    sells = [order for order in pending if order.side == "SELL"]
    buys = [order for order in pending if order.side == "BUY"]
    done = []

    for order in sells:
        price = open_prices.get(order.symbol)
        if price is None:
            continue                    # no trading today: try again tomorrow
        if broker.sell(day, order.symbol, price, order.reason):
            done.append("SOLD " + order.symbol + " at " + str(price))
        db.delete(order)

    # profits are reinvested: each buy gets the whole account value divided by 5
    money_per_stock = broker.total_value(open_prices) / STOCKS_TO_HOLD
    for order in buys:
        price = open_prices.get(order.symbol)
        if price is not None:
            if broker.buy(day, order.symbol, price, money_per_stock, order.reason):
                done.append("BOUGHT " + order.symbol + " at " + str(price))
        db.delete(order)                # a buy we could not make is dropped
    db.commit()
    return done


def plan_orders(db, day, to_sell, to_buy, reason):
    for symbol in to_sell:
        db.add(PendingOrder(symbol=symbol, side="SELL", reason=reason, decided_on=day))
    for symbol in to_buy:
        db.add(PendingOrder(symbol=symbol, side="BUY", reason=reason, decided_on=day))
    db.commit()


def run_daily_job(db, download=True):
    if download:
        update_prices(db)

    prices = load_prices(db)
    if prices.empty:
        return {"message": "No prices yet. Check the internet connection and run again."}

    day = prices["date"].max().date()
    if db.query(AccountDay).filter(AccountDay.date == day).first() is not None:
        return {"message": "Already done for " + str(day) + ". Nothing new to do."}

    broker = PaperBroker(db)
    first_run = db.query(AccountDay).count() == 0

    today = prices[prices["date"] == prices["date"].max()].set_index("symbol")
    trades_done = fill_pending_orders(db, broker, day, today["open"].to_dict())
    if len(trades_done) > 0:
        send_telegram("Paper trades on " + str(day) + ":\n" + "\n".join(trades_done))

    close, volume = make_tables(prices)
    numbers = latest_numbers(close, volume)
    health = market_health(numbers)
    held = broker.held_symbols()

    if not market_is_healthy(health):
        plan_orders(db, day, held, [], "weak market: move to cash")
        action = "weak market: selling everything tomorrow"
    elif is_rebalance_day(day) or first_run:
        ranked = rank_stocks(numbers)
        to_sell, to_buy = choose_trades(ranked, held)
        plan_orders(db, day, to_sell, to_buy, "rebalance")
        action = "rebalance: sell " + str(to_sell) + ", buy " + str(to_buy)
    else:
        action = "no rebalance today"

    broker.record_day(day, today["close"].to_dict(), health)
    return {"day": str(day), "market_health": health, "action": action,
            "account_value": round(broker.total_value(today["close"].to_dict()), 2)}


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        print(run_daily_job(session))
    finally:
        session.close()
