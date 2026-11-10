from config import COST_PER_SIDE, START_CASH
from db_models import Account, AccountDay, Order, Position, Trade


class PaperBroker:
    def __init__(self, db):
        self.db = db

    def account(self):
        account = self.db.query(Account).first()
        if account is None:
            account = Account(start_cash=START_CASH, cash=START_CASH)
            self.db.add(account)
            self.db.commit()
        return account

    def positions(self):
        return self.db.query(Position).all()

    def held_symbols(self):
        return [position.symbol for position in self.positions()]

    def total_value(self, prices):
        """Cash plus the value of every position. prices is a dict: symbol -> price."""
        total = self.account().cash
        for position in self.positions():
            price = prices.get(position.symbol, position.buy_price)
            total = total + position.shares * price
        return total

    def buy(self, day, symbol, price, money, reason):
        account = self.account()
        money = min(money, account.cash)
        shares = int(money // (price * (1 + COST_PER_SIDE)))
        if shares < 1:
            return False

        amount = shares * price
        cost = amount * COST_PER_SIDE
        account.cash = account.cash - amount - cost

        self.db.add(Position(symbol=symbol, shares=shares, buy_price=price, buy_date=day))
        self.db.add(Order(date=day, symbol=symbol, side="BUY", shares=shares, price=price,
                          cost=cost, reason=reason))
        self.db.commit()
        return True

    def sell(self, day, symbol, price, reason):
        position = self.db.query(Position).filter(Position.symbol == symbol).first()
        if position is None:
            return False

        account = self.account()
        amount = position.shares * price
        cost = amount * COST_PER_SIDE
        account.cash = account.cash + amount - cost

        # profit after the costs of both the buy and the sell
        bought_for = position.shares * position.buy_price * (1 + COST_PER_SIDE)
        profit = amount - cost - bought_for

        self.db.add(Order(date=day, symbol=symbol, side="SELL", shares=position.shares, price=price,
                          cost=cost, reason=reason))
        self.db.add(Trade(symbol=symbol, shares=position.shares, buy_date=position.buy_date,
                          buy_price=position.buy_price, sell_date=day, sell_price=price, profit=profit))
        self.db.delete(position)
        self.db.commit()
        return True

    def record_day(self, day, prices, health):
        total = self.total_value(prices)
        cash = self.account().cash
        self.db.add(AccountDay(date=day, cash=cash, holdings_value=total - cash, total=total,
                               market_health=health))
        self.db.commit()
