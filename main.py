import os
import logging
import random
import aiosqlite
import aiohttp
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import nest_asyncio
import asyncio

# Apply async patch
nest_asyncio.apply()

# Environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_TEMPLATE_ID = "895159"
GAME_KEY_DROP_URL = "https://neftyblocks.com/collection/games4punks1/drops/236466"
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"

# FastAPI
api = FastAPI()
pending_challenges = {}

logging.basicConfig(level=logging.INFO)

# --- CAPTCHA ---
async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a = random.randint(1, 10)
    b = random.randint(1, 10)
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
                await update.message.reply_text("❌ Incorrect. Try again.")
        except:
            await update.message.reply_text("❌ Please enter a number.")

# --- Wallet ---
async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /linkEwallet yourwaxwallet")
        return
    user_id = update.effective_user.id
    wallet = context.args[0]
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL)")
        await db.execute("INSERT OR REPLACE INTO linked_wallets (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
        await db.commit()
    await update.message.reply_text(f"🔗 WAX wallet {wallet} linked!")

# --- Verification ---
async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        await update.message.reply_text("❌ No wallet linked. Use /linkEwallet first.")
        return
    wallet = row[0]
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if data["data"]:
        await update.message.reply_text("✅ You own the GK3008 Game Key NFT!")
    else:
        await update.message.reply_text(f"🚫 You need the NFT:\n{GAME_KEY_DROP_URL}")

# --- Game Commands ---
async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_game_link(update, EMOJIS_INVADE_URL, context)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_game_link(update, SPACERUN_URL, context)

async def send_game_link(update, url, context):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        await update.message.reply_text("❌ Link your wallet with /linkEwallet")
        return
    wallet = row[0]
    asset_url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(asset_url) as resp:
            data = await resp.json()
    if data["data"]:
        await update.message.reply_text(f"🎮 Play now: {url}")
    else:
        await update.message.reply_text(f"🚫 NFT required. Buy here:\n{GAME_KEY_DROP_URL}")

# --- FastAPI Status ---
@api.get("/")
async def root(): return {"status": "running"}

@api.get("/health")
async def health(): return {"ok": True}

# --- Main ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("lfg", lfg))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ GK3008BOT is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())






