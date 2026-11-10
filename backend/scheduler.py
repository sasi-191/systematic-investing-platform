import threading
import time
from datetime import datetime

from alerts import send_telegram
from config import DAILY_JOB_HOURS
from daily_job import run_daily_job
from database import SessionLocal


def run_every_evening():
    done_on = None          # the day the job finished
    tried_at = None         # the last (day, hour) we tried

    while True:
        now = datetime.now()
        this_try = (now.date(), now.hour)
        is_weekday = now.weekday() < 5

        if is_weekday and now.hour in DAILY_JOB_HOURS and done_on != now.date() and tried_at != this_try:
            tried_at = this_try
            db = SessionLocal()
            try:
                result = run_daily_job(db)
            except Exception as error:
                result = {"message": "the job failed: " + str(error)}
            finally:
                db.close()

            if result.get("day") == str(now.date()):
                done_on = now.date()
                send_telegram("Daily job done for " + result["day"] + ": " + result["action"] +
                              ". Account value: Rs " + str(result["account_value"]))

        time.sleep(60)


def start_scheduler():
    # daemon=True: the thread stops when the server stops
    thread = threading.Thread(target=run_every_evening, daemon=True)
    thread.start()
