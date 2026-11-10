import pandas as pd

from config import (KEEP_IF_RANK_WITHIN, MARKET_HEALTHY_SHARE, MARKET_TRADED_VALUE, MIN_PRICE,
                    MIN_TRADED_VALUE, NEAR_HIGH, STOCKS_TO_HOLD)


def make_tables(prices):
    """Turns the long price list into two tables: one row per day, one column per stock."""
    close = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    volume = prices.pivot(index="date", columns="symbol", values="volume").sort_index()
    return close, volume


def latest_numbers(close, volume):
    """For every stock, the numbers the rules need, worked out for the last day."""
    numbers = pd.DataFrame()
    numbers["close"] = close.iloc[-1]
    numbers["days_of_data"] = close.tail(252).count()

    # how many rupees of the stock are traded in a day, on average over 6 months
    traded_value = close * volume
    numbers["traded_value"] = traded_value.tail(126).mean()

    numbers["average_50"] = close.tail(50).mean()
    numbers["average_200"] = close.tail(200).mean()
    numbers["high_1_year"] = close.tail(252).max()

    # the return over 6 months (126 trading days)
    if len(close) > 126:
        numbers["return_6_months"] = close.iloc[-1] / close.iloc[-127] - 1
    else:
        numbers["return_6_months"] = None

    # a fall of 35% in one day is almost always a split or a bonus issue, not a real fall
    daily_change = close / close.shift(1) - 1
    numbers["biggest_fall"] = daily_change.tail(130).min()
    return numbers


def market_health(numbers):
    """Share of big stocks that are above their 200 day average. None if there is not enough data."""
    big = numbers[(numbers["traded_value"] >= MARKET_TRADED_VALUE) & (numbers["days_of_data"] >= 200)]
    big = big.dropna(subset=["close", "average_200"])
    if len(big) == 0:
        return None

    above = big[big["close"] > big["average_200"]]
    return len(above) / len(big)


def market_is_healthy(health):
    if health is None:
        return True         # not enough history yet: do not block buying
    return health >= MARKET_HEALTHY_SHARE


def rank_stocks(numbers):
    """Stocks that pass every check, best first, by their 6 month return."""
    good = numbers.dropna(subset=["close", "return_6_months"])
    good = good[good["days_of_data"] >= 200]
    good = good[good["traded_value"] >= MIN_TRADED_VALUE]             # easy to buy and sell
    good = good[good["close"] >= MIN_PRICE]                           # not a very cheap share
    good = good[good["close"] > good["average_50"]]                   # in an uptrend
    good = good[good["close"] >= NEAR_HIGH * good["high_1_year"]]     # close to its 1 year high
    good = good[good["biggest_fall"] > -0.35]                         # no split in the data

    return good["return_6_months"].sort_values(ascending=False)


def choose_trades(ranked, held_symbols):
    """Which stocks to sell and which to buy on a rebalance day."""
    keep_list = list(ranked.index[:KEEP_IF_RANK_WITHIN])

    to_sell = []
    staying = []
    for symbol in held_symbols:
        if symbol in keep_list:
            staying.append(symbol)
        else:
            to_sell.append(symbol)

    free_slots = STOCKS_TO_HOLD - len(staying)
    to_buy = []
    for symbol in ranked.index:
        if len(to_buy) >= free_slots:
            break
        if symbol not in held_symbols:
            to_buy.append(symbol)
    return to_sell, to_buy


def is_rebalance_day(day):
    """Every second Friday (Fridays in even-numbered weeks of the year)."""
    day = pd.Timestamp(day)
    return day.weekday() == 4 and day.isocalendar().week % 2 == 0
