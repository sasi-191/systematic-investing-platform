import json
import os
from datetime import date

from fyers_apiv3 import fyersModel

from config import FYERS_APP_ID, FYERS_REDIRECT_URI, FYERS_SECRET_KEY, FYERS_TOKEN_FILE


def is_configured():
    return FYERS_APP_ID != "" and FYERS_SECRET_KEY != ""


def make_session():
    return fyersModel.SessionModel(
        client_id=FYERS_APP_ID,
        secret_key=FYERS_SECRET_KEY,
        redirect_uri=FYERS_REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code",
    )


def login_url():
    return make_session().generate_authcode()


def save_token_from_code(auth_code):
    """After you log in, Fyers sends a code. We swap it for the day's token. Returns True if it worked."""
    session = make_session()
    session.set_token(auth_code)
    response = session.generate_token()
    if response.get("s") != "ok":
        return False

    with open(FYERS_TOKEN_FILE, "w") as file:
        json.dump({"access_token": response["access_token"], "date": str(date.today())}, file)
    return True


def read_token():
    if not os.path.exists(FYERS_TOKEN_FILE):
        return None
    with open(FYERS_TOKEN_FILE) as file:
        return json.load(file)


def token_is_from_today():
    token = read_token()
    return token is not None and token.get("date") == str(date.today())


def make_fyers():
    token = read_token()
    return fyersModel.FyersModel(client_id=FYERS_APP_ID, token=token["access_token"], is_async=False, log_path="")


def live_prices(symbols):
    """symbol -> live price from Fyers. An empty dict if we are not logged in today or Fyers fails."""
    if not token_is_from_today() or len(symbols) == 0:
        return {}

    prices = {}
    try:
        fyers = make_fyers()
        # Fyers takes at most 50 symbols in one request
        for start in range(0, len(symbols), 50):
            group = symbols[start:start + 50]
            names = []
            for symbol in group:
                names.append("NSE:" + symbol + "-EQ")
            response = fyers.quotes(data={"symbols": ",".join(names)})

            for item in response.get("d", []):
                price = item.get("v", {}).get("lp")
                if price:
                    symbol = item["n"].replace("NSE:", "").replace("-EQ", "")
                    prices[symbol] = float(price)
    except Exception:
        return {}
    return prices
