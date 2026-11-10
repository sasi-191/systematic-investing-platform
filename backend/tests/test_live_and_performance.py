from fastapi.testclient import TestClient

from alerts import send_telegram
from config import ADMIN_PASSWORD, ADMIN_USERNAME
from database import Base, engine
from live_broker import check_order
from main import app


def logged_in_client(client):
    answer = client.post("/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    return {"Authorization": "Bearer " + answer.json()["access_token"]}


def test_live_orders_need_confirm_and_are_locked():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        headers = logged_in_client(client)

        no_confirm = client.post("/live/place-orders", json={"confirm": "yes"}, headers=headers)
        assert "Type CONFIRM" in no_confirm.json()["results"][0]

        locked = client.post("/live/place-orders", json={"confirm": "CONFIRM"}, headers=headers)
        assert "locked" in locked.json()["results"][0]


def test_order_safety_checks():
    # live trading is off in the tests, so every order is refused
    assert check_order("BUY", 10, 100) is not None


def test_performance_and_fyers_status_work_with_no_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        headers = logged_in_client(client)
        assert client.get("/performance", headers=headers).json() == {"chart": [], "months": []}
        status = client.get("/fyers/status", headers=headers).json()
        assert status["logged_in_today"] is False
        assert client.get("/positions?live=true", headers=headers).json() == []


def test_telegram_does_nothing_without_settings():
    assert send_telegram("hello") is False
