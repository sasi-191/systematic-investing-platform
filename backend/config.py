import os

from dotenv import load_dotenv

# read the values in the .env file into the environment
load_dotenv()

# ---------- app settings ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./investing.db")
SECRET_KEY = os.getenv("SECRET_KEY", "please-change-this-secret")
ALGORITHM = "HS256"
TOKEN_MINUTES = 60

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

FRONTEND_URL = "http://localhost:5173"

# ---------- Fyers broker (for live prices and live orders) ----------
FYERS_APP_ID = os.getenv("FYERS_APP_ID", "")
FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "")
FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "http://127.0.0.1:8000/fyers/callback")
FYERS_TOKEN_FILE = "fyers_token.json"

# real orders are sent ONLY when this is "true" in .env
LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"
MAX_ORDER_VALUE = 25000             # one real order can never be bigger than Rs 25,000

# ---------- Telegram alerts ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------- the automatic evening job ----------
AUTO_DAILY_JOB = os.getenv("AUTO_DAILY_JOB", "true").lower() == "true"
DAILY_JOB_HOURS = [19, 20, 21, 22]  # NSE publishes the daily file in the evening: we try each of these hours

# ---------- strategy settings ----------
START_CASH = 100000                 # the paper account starts with Rs 1,00,000
STOCKS_TO_HOLD = 5                  # how many stocks we hold at the same time
KEEP_IF_RANK_WITHIN = 10            # a stock we hold stays while it ranks in the top 10
MIN_TRADED_VALUE = 200000000        # Rs 20 crore traded per day on average
MIN_PRICE = 20                      # skip very cheap shares
NEAR_HIGH = 0.75                    # price must be at least 75% of its 1 year high

# the market check: what share of the big stocks is above its 200 day average
MARKET_TRADED_VALUE = 100000000     # stocks with Rs 10 crore a day are used for this check
MARKET_HEALTHY_SHARE = 0.40         # below 40% the market is weak: we sell everything

COST_PER_SIDE = 0.003               # brokerage, taxes and slippage, 0.3% for each buy or sell
CALENDAR_DAYS_OF_HISTORY = 400      # about 270 trading days, enough for every indicator
