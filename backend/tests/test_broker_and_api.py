from datetime import date

from fastapi.testclient import TestClient

from broker import PaperBroker
from config import ADMIN_PASSWORD, ADMIN_USERNAME, COST_PER_SIDE, START_CASH
from database import Base, SessionLocal, engine
from main import app


def fresh_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_buy_and_sell_update_cash():
    db = fresh_database()
    broker = PaperBroker(db)

    broker.buy(date(2026, 1, 5), "ABC", price=100, money=10000, reason="test")
    position = broker.positions()[0]
    assert position.shares == 99                 # 10,000 cannot buy 100 shares after costs
    cash_after_buy = START_CASH - 99 * 100 * (1 + COST_PER_SIDE)
    assert round(broker.account().cash, 2) == round(cash_after_buy, 2)

    broker.sell(date(2026, 1, 20), "ABC", price=110, reason="test")
    assert broker.positions() == []
    assert broker.account().cash > START_CASH     # a 10% rise is a profit even after costs
    db.close()


def test_login_and_protected_route():
    fresh_database()
    with TestClient(app) as client:
        assert client.get("/summary").status_code == 401       # no token

        wrong = client.post("/login", data={"username": ADMIN_USERNAME, "password": "wrong"})
        assert wrong.status_code == 401

        right = client.post("/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
        token = right.json()["access_token"]
        answer = client.get("/summary", headers={"Authorization": "Bearer " + token})
        assert answer.status_code == 200
        assert answer.json()["total_value"] == START_CASH
