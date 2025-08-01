import os
import logging
import random
import aiosqlite
import aiohttp
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)
import nest_asyncio
import asyncio

# --- Setup ---
nest_asyncio.apply()
BOT_TOKEN = os.getenv("BOT_TOKEN")

REQUIRED_TEMPLATE_ID = "895159"
GAME_KEY_DROP_URL = "https://neftyblocks.com/collection/games4punks1/drops/236466"
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"

logging.basicConfig(level=logging.INFO)

api = FastAPI()
pending_challenges = {}

# --- CAPTCHA ---
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
        except:
            await update.message.reply_text("❌ Enter a number.")
    else:
        await update.message.reply_text("❌ Use /lfg to verify first.")

# --- Wallet Linking ---
async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /linkEwallet yourwaxwallet")
        return
    wallet = context.args[0]
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL)")
        await db.execute("INSERT OR REPLACE INTO linked_wallets (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
        await db.commit()
    await update.message.reply_text(f"🔗 WAX wallet {wallet} linked!")

async def unlink_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("DELETE FROM linked_wallets WHERE telegram_id = ?", (user_id,))
        await db.commit()
    await update.message.reply_text("❌ Wallet unlinked.")

# --- NFT Check ---
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
        await update.message.reply_text(f"🚫 You need the NFT to play. Buy here:\n{GAME_KEY_DROP_URL}")

# --- Game Launch ---
async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await launch_game(update, EMOJIS_INVADE_URL)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await launch_game(update, SPACERUN_URL)

async def launch_game(update: Update, game_url: str):
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
        await update.message.reply_text(f"🎮 Launch game:\n{game_url}")
    else:
        await update.message.reply_text(f"🚫 NFT required.\nBuy here:\n{GAME_KEY_DROP_URL}")

# --- Welcome ---
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_user = update.message.new_chat_members[0]
    welcome = (
        f"🎉 Welcome {new_user.first_name} to the GKniftyHEADS Crew!\n\n"
        f"🎮 Play Web3 games:\n"
        f"/plaE@GAMES4PUNKSBOT – Emojis Invade\n"
        f"/spacerun@GAMES4PUNKSBOT – Spacerun3008\n\n"
        f"🗝 NFT Required: GK3008 Game Key\n"
        f"🔗 Buy: {GAME_KEY_DROP_URL}\n"
        f"📲 Link: /linkEwallet\n"
        f"🧠 Solve: /lfg"
    )
    await update.message.reply_text(welcome)

# --- FastAPI ---
@api.get("/")
async def root():
    return {"status": "GK3008 Bot is running"}

@api.get("/health")
async def health():
    return {"status": "ok"}

# --- Run Bot ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("lfg", lfg))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_wallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    print("✅ GAMES4PUNKSBOT is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())






