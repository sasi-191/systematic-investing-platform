from alerts import send_telegram
from broker import PaperBroker
from config import LIVE_TRADING_ENABLED, MAX_ORDER_VALUE, STOCKS_TO_HOLD
from db_models import PendingOrder, Position
from fyers_client import live_prices, make_fyers, token_is_from_today
from nse_data import latest_closes


def check_order(side, shares, price):
    """Returns None if the order is allowed, or the reason it is not."""
    if not LIVE_TRADING_ENABLED:
        return "live trading is locked (LIVE_TRADING_ENABLED is not true)"
    if shares < 1:
        return "less than one share"
    if shares * price > MAX_ORDER_VALUE:
        return "bigger than the safety limit of Rs " + str(MAX_ORDER_VALUE)
    return None


def send_order(fyers, symbol, side, shares):
    order = {
        "symbol": "NSE:" + symbol + "-EQ",
        "qty": shares,
        "type": 2,                              # 2 = market order
        "side": 1 if side == "BUY" else -1,     # 1 = buy, -1 = sell
        "productType": "CNC",                   # delivery, not intraday
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
    }
    response = fyers.place_order(data=order)
    return response.get("s") == "ok", response.get("message", "")


def place_pending_orders(db):
    """Sends today's planned orders to Fyers. Returns one line of text per order."""
    if not LIVE_TRADING_ENABLED:
        return ["Live trading is locked. Set LIVE_TRADING_ENABLED=true in .env to use it."]
    if not token_is_from_today():
        return ["Please log in to Fyers first (once a day)."]

    pending = db.query(PendingOrder).all()
    if len(pending) == 0:
        return ["There are no planned orders right now."]

    symbols = [order.symbol for order in pending]
    prices = live_prices(symbols)
    money_per_stock = PaperBroker(db).total_value(latest_closes(db)) / STOCKS_TO_HOLD
    fyers = make_fyers()

    results = []
    for order in pending:
        price = prices.get(order.symbol)
        if price is None:
            results.append(order.symbol + ": no live price, skipped")
            continue

        if order.side == "SELL":
            position = db.query(Position).filter(Position.symbol == order.symbol).first()
            shares = position.shares if position else 0
        else:
            shares = int(money_per_stock // price)

        problem = check_order(order.side, shares, price)
        if problem:
            results.append(order.symbol + ": not sent, " + problem)
            continue

        sent, message = send_order(fyers, order.symbol, order.side, shares)
        if sent:
            results.append(order.side + " " + str(shares) + " " + order.symbol + ": sent to Fyers")
        else:
            results.append(order.symbol + ": Fyers refused it, " + message)

    send_telegram("Live orders:\n" + "\n".join(results))
    return results
