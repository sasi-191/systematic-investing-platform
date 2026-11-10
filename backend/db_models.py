from sqlalchemy import Column, Date, Float, Integer, String, UniqueConstraint

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Price(Base):
    """One day of one stock: open, high, low, close and volume."""
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("date", "symbol"),)

    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


class Account(Base):
    """The paper account. There is only one row."""
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    start_cash = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)


class Position(Base):
    """A stock we hold right now."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    shares = Column(Integer, nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_date = Column(Date, nullable=False)


class PendingOrder(Base):
    """An order decided in the evening. It is filled at the next day's open price."""
    __tablename__ = "pending_orders"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)        # "BUY" or "SELL"
    reason = Column(String)
    decided_on = Column(Date, nullable=False)


class Order(Base):
    """Every buy and every sell that really happened in the paper account."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    shares = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    reason = Column(String)


class Trade(Base):
    """A finished trade: one buy and its sell."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    shares = Column(Integer, nullable=False)
    buy_date = Column(Date, nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_date = Column(Date, nullable=False)
    sell_price = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)


class AccountDay(Base):
    """The value of the account at the end of each trading day."""
    __tablename__ = "account_history"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    cash = Column(Float, nullable=False)
    holdings_value = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    market_health = Column(Float)        # share of big stocks above their 200 day average
