
from fastapi import FastAPI, Query
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

DB_NAME = "gkbot.db"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/verify-wallet")
def verify_wallet(wallet: str = Query(..., min_length=5, max_length=20)):
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute("""
            SELECT verified FROM verified_users
            WHERE wallet = ? AND verified = 1
        """, (wallet,)).fetchone()

    if result:
        return {"status": "ok", "verified": True}
    else:
        return {
            "status": "error",
            "verified": False,
            "reason": "Wallet not verified via Telegram bot with Game Key."
        }
