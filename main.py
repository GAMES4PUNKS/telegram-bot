import logging
import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import nest_asyncio
import threading

# Apply asyncio patch
nest_asyncio.apply()

# Setup
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")  # For FastAPI endpoint protection
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", 1019741898))

DB_FILE = "gkbot.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    wallet TEXT,
    plays INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0
)
""")
conn.commit()

# Game URLs
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Telegram App
app = ApplicationBuilder().token(BOT_TOKEN).build()
captcha_answers = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the official GK3008 Game Bot!\n\n"
        "🎮 Available Games:\n"
        "/plaE – Play Emojis Invade (NFT required)\n"
        "/spacerun – Play Spacerun3008 (NFT required)\n"
        "/linkEwallet – Link your WAX wallet\n"
        "/verifyEkey – Verify your NFT game key\n"
        "/unlinkEwallet – Unlink your WAX wallet"
    )

# /plaE
async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("SELECT verified FROM users WHERE telegram_id = ?", (uid,))
    row = cur.fetchone()
    if row and row[0] == 1:
        await update.message.reply_text(
            "🎮 Click to play Emojis Invade:", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play", url=EMOJIS_INVADE_URL)]])
        )
    else:
        await update.message.reply_text("❌ You must verify your NFT key first using /verifyEkey.")

# /spacerun
async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("SELECT verified FROM users WHERE telegram_id = ?", (uid,))
    row = cur.fetchone()
    if row and row[0] == 1:
        await update.message.reply_text(
            "🚀 Click to play Spacerun3008:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play", url=SPACERUN_URL)]])
        )
    else:
        await update.message.reply_text("❌ You must verify your NFT key first using /verifyEkey.")

# /linkEwallet step 1 – CAPTCHA
async def linkEwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    answer = a + b
    captcha_answers[uid] = answer
    await update.message.reply_text(f"🧠 To continue, solve this: {a} + {b} = ?")
    return 1

# Step 2 – answer check
async def handle_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        if int(update.message.text) == captcha_answers.get(uid):
            await update.message.reply_text("✅ Correct. Now send your WAX wallet address:")
            return 2
        else:
            await update.message.reply_text("❌ Incorrect. Try /linkEwallet again.")
            return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Invalid input. Try /linkEwallet again.")
        return ConversationHandler.END

# Step 3 – get wallet
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    wallet = update.message.text.strip()
    cur.execute("INSERT OR REPLACE INTO users (telegram_id, wallet) VALUES (?, ?)", (uid, wallet))
    conn.commit()
    await update.message.reply_text(f"✅ Wallet {wallet} linked successfully.")
    return ConversationHandler.END

# /unlinkEwallet
async def unlinkEwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("UPDATE users SET wallet = NULL WHERE telegram_id = ?", (uid,))
    conn.commit()
    await update.message.reply_text("🗑️ WAX wallet unlinked.")

# /verifyEkey
async def verifyEkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 To verify your Game Key NFT:\n\n"
        "1. Make sure your WAX wallet is linked via /linkEwallet\n"
        "2. Visit: https://wax.atomichub.io/explorer/account/yourwallet\n"
        "3. Check if you hold this NFT: [GK3008 Game Key](https://wax.atomichub.io/explorer/template/wax-mainnet/games4punks1/GK3008-Game-Key_895159)\n\n"
        "❓ Need one? Buy here: https://neftyblocks.com/collection/games4punks1/drops/236466\n\n"
        "Once confirmed, your NFT will be verified manually or automatically soon."
    )

# /players (admin)
async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_CHAT_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        await update.message.reply_text(f"👥 Total linked users: {total}")

# FastAPI setup
api = FastAPI()

@api.middleware("http")
async def api_key_check(request: Request, call_next):
    key = request.headers.get("X-API-Key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)

@api.get("/api/users")
async def get_users():
    cur.execute("SELECT telegram_id, wallet, plays, verified FROM users")
    data = cur.fetchall()
    return JSONResponse(content={"users": data})

# Run Telegram bot
async def telegram_main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("linkEwallet", linkEwallet)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_captcha)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("unlinkEwallet", unlinkEwallet))
    app.add_handler(CommandHandler("verifyEkey", verifyEkey))
    app.add_handler(CommandHandler("players", players))
    app.add_handler(conv_handler)

    print("✅ Telegram bot running...")
    await app.run_polling()

# Launch both FastAPI + Telegram
def run_all():
    thread = threading.Thread(target=uvicorn.run, args=(api,), kwargs={"host": "0.0.0.0", "port": 8000})
    thread.start()
    import asyncio
    asyncio.run(telegram_main())

if __name__ == "__main__":
    run_all()


if __name__ == "__main__":
    Thread(target=start_api).start()
    asyncio.run(run_bot())

