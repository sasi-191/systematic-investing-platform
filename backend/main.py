from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import hash_password
from config import ADMIN_PASSWORD, ADMIN_USERNAME, AUTO_DAILY_JOB, FRONTEND_URL
from database import Base, SessionLocal, engine
from db_models import User
from routes import auth_routes, fyers_routes, portfolio_routes
from scheduler import start_scheduler


def create_admin_user():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == ADMIN_USERNAME).first() is None:
            db.add(User(username=ADMIN_USERNAME, hashed_password=hash_password(ADMIN_PASSWORD)))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app):
    # runs once when the server starts
    Base.metadata.create_all(bind=engine)
    create_admin_user()
    if AUTO_DAILY_JOB:
        start_scheduler()
    yield


app = FastAPI(title="Systematic Investing Platform", lifespan=lifespan)

# lets the React app (running on port 5173) call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(portfolio_routes.router)
app.include_router(fyers_routes.router)


@app.get("/")
def home():
    return {"message": "Systematic Investing Platform is running. Open /docs to see the API."}
