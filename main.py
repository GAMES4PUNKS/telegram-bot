import os
import logging
import random
import aiosqlite
import aiohttp
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
import nest_asyncio
import asyncio

# Apply for Jupyter/notebook compatibility
nest_asyncio.apply()

# --- Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_TEMPLATE_ID = "895159"
GAME_KEY_DROP_URL = "https://neftyblocks.com/collection/games4punks1/drops/236466"
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"

logging.basicConfig(level=logging.INFO)

# --- FastAPI ---
api = FastAPI()

@api.get("/")
async def root():
    return {"status": "GK3008BOT running"}

# --- In-memory math challenge store ---
pending_challenges = {}

# --- Command: /lfg (Math CAPTCHA) ---
async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    answer = a + b
    pending_challenges[user_id] = answer
    await update.message.reply_text(f"🧠 Solve this: What is {a} + {b}?")

# --- Handle response to CAPTCHA ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in pending_challenges:
        try:
            user_answer = int(update.message.text.strip())
            if user_answer == pending_challenges[user_id]:
                del pending_challenges[user_id]
                await update.message.reply_text("✅ Verified! Use /plaE or /spacerun to begin.")
            else:
                await update.message.reply_text("❌ Wrong answer. Try again.")
        except:
            await update.message.reply_text("❌ Please enter a number.")
    else:
        await update.message.reply_text("Use /lfg to start.")

# --- Command: /linkEwallet <wallet> ---
async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /linkEwallet yourwaxwallet")
        return
    wallet = context.args[0]
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT)")
        await db.execute("INSERT OR REPLACE INTO linked_wallets (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
        await db.commit()
    await update.message.reply_text(f"🔗 WAX wallet {wallet} linked!")

# --- Command: /verifyEkey ---
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

# --- Command: /plaE ---
async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("⚙️ [plaE] Command triggered")
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if not result:
        print("❌ [plaE] No wallet linked")
        await update.message.reply_text("❌ Link your wallet first with /linkEwallet.")
        return

    wallet = result[0]
    print(f"🔗 [plaE] Checking wallet: {wallet}")
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if data["data"]:
        print("✅ [plaE] NFT found. Sending game URL.")
        await update.message.reply_text(f"🎮 Play Emojis Invade:\n{EMOJIS_INVADE_URL}")
    else:
        print("🚫 [plaE] NFT not found")
        await update.message.reply_text(f"🚫 NFT required.\nBuy here:\n{GAME_KEY_DROP_URL}")

# --- Command: /spacerun ---
async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("⚙️ [spacerun] Command triggered")
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if not result:
        print("❌ [spacerun] No wallet linked")
        await update.message.reply_text("❌ Link your wallet first with /linkEwallet.")
        return

    wallet = result[0]
    print(f"🔗 [spacerun] Checking wallet: {wallet}")
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if data["data"]:
        print("✅ [spacerun] NFT found. Sending game URL.")
        await update.message.reply_text(f"🚀 Play Spacerun3008:\n{SPACERUN_URL}")
    else:
        print("🚫 [spacerun] NFT not found")
        await update.message.reply_text(f"🚫 NFT required.\nBuy here:\n{GAME_KEY_DROP_URL}")

# --- Main Bot Runner ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("lfg", lfg))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot is running via polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())







