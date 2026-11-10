from datetime import date

import pandas as pd

from strategy import choose_trades, is_rebalance_day, latest_numbers, market_health, rank_stocks


def make_fake_prices():
    """300 days of 3 made-up stocks: one rising, one flat, one falling. All very liquid."""
    days = pd.bdate_range("2024-01-01", periods=300)
    close = pd.DataFrame({
        "RISING": [100 + day for day in range(300)],
        "FLAT": [100.0] * 300,
        "FALLING": [400 - day for day in range(300)],
    }, index=days)
    volume = pd.DataFrame(10000000.0, index=days, columns=close.columns)
    return close, volume


def test_rising_stock_ranks_first():
    close, volume = make_fake_prices()
    ranked = rank_stocks(latest_numbers(close, volume))
    assert list(ranked.index) == ["RISING"]      # flat and falling stocks fail the uptrend check


def test_market_health_is_a_share():
    close, volume = make_fake_prices()
    health = market_health(latest_numbers(close, volume))
    assert health == 1 / 3                       # only the rising stock is above its 200 day average


def test_choose_trades_keeps_good_stocks():
    ranked = pd.Series([0.9, 0.8, 0.7], index=["A", "B", "C"])
    to_sell, to_buy = choose_trades(ranked, held_symbols=["A", "OLD"])
    assert to_sell == ["OLD"]
    assert "A" not in to_buy
    assert to_buy == ["B", "C"]


def test_rebalance_is_every_second_friday():
    assert is_rebalance_day(date(2026, 1, 9)) != is_rebalance_day(date(2026, 1, 16))
    assert is_rebalance_day(date(2026, 1, 12)) is False      # a Monday
