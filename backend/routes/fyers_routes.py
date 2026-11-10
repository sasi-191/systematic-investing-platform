from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from auth import get_current_user
from config import FRONTEND_URL, LIVE_TRADING_ENABLED
from fyers_client import is_configured, login_url, save_token_from_code, token_is_from_today

router = APIRouter(tags=["fyers"])


@router.get("/fyers/status", dependencies=[Depends(get_current_user)])
def fyers_status():
    return {
        "configured": is_configured(),
        "logged_in_today": token_is_from_today(),
        "live_trading_enabled": LIVE_TRADING_ENABLED,
    }


@router.get("/fyers/login-url", dependencies=[Depends(get_current_user)])
def fyers_login_url():
    if not is_configured():
        raise HTTPException(status_code=400, detail="Add FYERS_APP_ID and FYERS_SECRET_KEY to .env first")
    return {"url": login_url()}


@router.get("/fyers/callback")
def fyers_callback(auth_code: str = ""):
    """Fyers sends the browser here after you log in. We save the day's token and go back to the dashboard."""
    if auth_code and save_token_from_code(auth_code):
        return RedirectResponse(FRONTEND_URL + "/?fyers=ok")
    return RedirectResponse(FRONTEND_URL + "/?fyers=failed")
