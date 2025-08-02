import os
import logging
import random
import aiosqlite
import aiohttp
import asyncio
import nest_asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

# Load Bot Token from Render Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_TEMPLATE_ID = "895159"

# URLs
GAME_KEY_DROP_URL = "https://neftyblocks.com/collection/games4punks1/drops/236466"
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"

# Asyncio Nest for FastAPI + Polling
nest_asyncio.apply()

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI Instance
api = FastAPI()

@api.get("/")
async def root():
    return {"status": "GK3008BOT is Running"}

# In-Memory CAPTCHA Challenges
pending_challenges = {}

# Telegram Handlers
async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a, b = random.randint(1, 10), random.randint(1, 10)
    pending_challenges[user_id] = a + b
    await update.message.reply_text(f"🧠 Solve this: What is {a} + {b}?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in pending_challenges:
        try:
            if int(update.message.text.strip()) == pending_challenges[user_id]:
                del pending_challenges[user_id]
                await update.message.reply_text("✅ Verified! Use /plaE or /spacerun to begin.")
            else:
                await update.message.reply_text("❌ Wrong answer. Try again.")
        except ValueError:
            await update.message.reply_text("❌ Please enter a number.")
    else:
        await update.message.reply_text("Use /lfg to start verification.")

async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /linkEwallet yourwaxwallet")
        return
    wallet = context.args[0]
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL)"
        )
        await db.execute(
            "INSERT OR REPLACE INTO linked_wallets (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet)
        )
        await db.commit()
    await update.message.reply_text(f"🔗 WAX wallet {wallet} linked!")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    if not result:
        await update.message.reply_text("❌ No wallet linked. Use /linkEwallet first.")
        return
    wallet = result[0]
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if data["data"]:
        await update.message.reply_text("✅ You own the required GK3008 Game Key NFT!")
    else:
        await update.message.reply_text(f"🚫 You need the NFT to play:\n{GAME_KEY_DROP_URL}")

async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await game_link_handler(update, EMOJIS_INVADE_URL)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await game_link_handler(update, SPACERUN_URL)

async def game_link_handler(update: Update, game_url: str):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    if not result:
        await update.message.reply_text("❌ Link your wallet first with /linkEwallet.")
        return
    wallet = result[0]
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if data["data"]:
        await update.message.reply_text(f"🎮 Play here:\n{game_url}")
    else:
        await update.message.reply_text(f"🚫 NFT required. Buy here:\n{GAME_KEY_DROP_URL}")

# Run Telegram Polling as Background Task
async def telegram_polling():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL)"
        )
        await db.commit()

    # Command Handlers
    application.add_handler(CommandHandler("lfg", lfg))
    application.add_handler(CommandHandler("linkEwallet", link_wallet))
    application.add_handler(CommandHandler("verifyEkey", verify_ekey))
    application.add_handler(CommandHandler("plaE", plaE))
    application.add_handler(CommandHandler("spacerun", spacerun))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    await application.run_polling()

# Start FastAPI + Polling Together
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_polling())

