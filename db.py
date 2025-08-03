# db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
conn.autocommit = True

# INIT DB
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS linked_wallets (
            telegram_id BIGINT PRIMARY KEY,
            wallet TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verified_users (
            telegram_id BIGINT PRIMARY KEY,
            wallet TEXT NOT NULL,
            verified BOOLEAN DEFAULT FALSE
        );
    """)

def link_wallet(telegram_id: int, wallet: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO linked_wallets (telegram_id, wallet)
            VALUES (%s, %s)
            ON CONFLICT (telegram_id) DO UPDATE SET wallet = EXCLUDED.wallet;
        """, (telegram_id, wallet))

def get_wallet(telegram_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))
        row = cur.fetchone()
        return row['wallet'] if row else None

def unlink_wallet(telegram_id: int):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))

def set_verified(telegram_id: int, wallet: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO verified_users (telegram_id, wallet, verified)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (telegram_id) DO UPDATE SET verified = TRUE, wallet = EXCLUDED.wallet;
        """, (telegram_id, wallet))

def is_wallet_verified(wallet: str):
    with conn.cursor() as cur:
        cur.execute("SELECT verified FROM verified_users WHERE wallet = %s AND verified = TRUE", (wallet,))
        row = cur.fetchone()
        return bool(row)
