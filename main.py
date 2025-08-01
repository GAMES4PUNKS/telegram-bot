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

nest_asyncio.apply()

# Environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Constants
REQUIRED_TEMPLATE_ID = "895159"
GAME_KEY_DROP_URL = "https://neftyblocks.com/collection/games4punks1/drops/236466"
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI app
api = FastAPI()

# In-memory CAPTCHA tracker
pending_challenges = {}

# --- Commands ---
async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a, b = random.randint(1, 10), random.randint(1, 10)
    pending_challenges[user_id] = a + b
    await update.message.reply_text(f"🧠 Solve this to continue: What is {a} + {b}?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in pending_challenges:
        try:
            answer = int(update.message.text.strip())
            if answer == pending_challenges[user_id]:
                del pending_challenges[user_id]
                await update.message.reply_text("✅ Verified! Use /plaE or /spacerun to begin.")
            else:
                await update.message.reply_text("❌ Wrong answer. Try again.")
        except:
            await update.message.reply_text("❌ Enter a number.")
    else:
        await update.message.reply_text("❌ Use /lfg to start verification.")

async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /linkEwallet yourwaxwallet")
        return
    wallet = context.args[0]
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS linked_wallets (
                telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL
            )
        """)
        await db.execute("INSERT OR REPLACE INTO linked_wallets (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
        await db.commit()
    await update.message.reply_text(f"🔗 WAX wallet {wallet} linked!")

async def unlink_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("DELETE FROM linked_wallets WHERE telegram_id = ?", (user_id,))
        await db.commit()
    await update.message.reply_text("❌ Wallet unlinked.")

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
        await update.message.reply_text(f"🚫 NFT not found. Buy here:\n{GAME_KEY_DROP_URL}")

async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_game_link(update, EMOJIS_INVADE_URL)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_game_link(update, SPACERUN_URL)

async def send_game_link(update: Update, game_url):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    if not result:
        await update.message.reply_text("❌ Link your wallet with /linkEwallet.")
        return
    wallet = result[0]
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if data["data"]:
        await update.message.reply_text(f"🎮 Play: {game_url}")
    else:
        await update.message.reply_text(f"🚫 NFT required.\nBuy here:\n{GAME_KEY_DROP_URL}")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    welcome = (
        f"🎉 Welcome {new_member.first_name} to the GKniftyHEADS Channel!\n\n"
        f"🎮 Play our Web3 games:\n"
        f"- /plaE – Emojis Invade\n"
        f"- /spacerun – Spacerun3008\n\n"
        f"🗝 NFT Required: GK3008 Game Key\n"
        f"🔗 Buy here: {GAME_KEY_DROP_URL}\n"
        f"📲 Link wallet: /linkEwallet\n"
        f"🧠 Start with /lfg"
    )
    await update.message.reply_text(welcome)

# --- FastAPI Endpoints ---
@api.get("/")
async def root():
    return {"status": "GK3008 Bot is online"}

@api.get("/health")
async def health():
    return {"status": "ok"}

# --- Main Bot Runner ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("lfg", lfg))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_wallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    print("✅ GK3008 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())





