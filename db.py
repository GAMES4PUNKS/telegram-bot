
import sqlite3

DB_NAME = "gkbot.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS linked_wallets (
            telegram_id INTEGER PRIMARY KEY,
            wallet TEXT NOT NULL
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS verified_users (
            telegram_id INTEGER PRIMARY KEY,
            wallet TEXT NOT NULL,
            verified INTEGER DEFAULT 0
        )""")

def link_wallet(telegram_id: int, wallet: str):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""REPLACE INTO linked_wallets (telegram_id, wallet)
                         VALUES (?, ?)""", (telegram_id, wallet))

def get_wallet(telegram_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute("""SELECT wallet FROM linked_wallets
                                 WHERE telegram_id = ?""", (telegram_id,)).fetchone()
        return result[0] if result else None

def unlink_wallet(telegram_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""DELETE FROM linked_wallets WHERE telegram_id = ?""", (telegram_id,))

def set_verified(telegram_id: int, wallet: str):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO verified_users (telegram_id, wallet, verified)
            VALUES (?, ?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET verified = 1, wallet = ?
        """, (telegram_id, wallet))

def is_wallet_verified(wallet: str):
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute("""
            SELECT verified FROM verified_users
            WHERE wallet = ? AND verified = 1
        """, (wallet,)).fetchone()
        return bool(result)
