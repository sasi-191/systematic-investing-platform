import os

# the tests use their own small database file, never the real one,
# and they never send real orders, Telegram messages or start the evening job
os.environ["DATABASE_URL"] = "sqlite:///./test_investing.db"
os.environ["AUTO_DAILY_JOB"] = "false"
os.environ["LIVE_TRADING_ENABLED"] = "false"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
