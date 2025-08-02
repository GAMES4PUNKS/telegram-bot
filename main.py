import os
import logging
import random
import aiosqlite
import aiohttp
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
import nest_asyncio
import asyncio
import uvicorn

# Patch asyncio for nested loops
nest_asyncio.apply()

# Configs
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_TEMPLATE_ID = "895159"
GAME_KEY_DROP_URL = "https://neftyblocks.com/collection/games4punks1/drops/236466"
EMOJIS_INVADE_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_URL = "https://games4punks.github.io/spacerun3008/"
OWNER_CHAT_ID = 1019741898

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI App
api = FastAPI()

@api.get("/")
async def root():
    return {"status": "GK3008BOT running"}

# In-Memory States
pending_challenges = {}
verified_users = set()
players = set()

# --- Telegram Bot Handlers ---
async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    pending_challenges[user_id] = a + b
    await update.message.reply_text(f"🧒 Solve this: What is {a} + {b}?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in pending_challenges:
        try:
            if int(text) == pending_challenges[user_id]:
                del pending_challenges[user_id]
                verified_users.add(user_id)
                await update.message.reply_text("✅ Verified! Now link your wallet with /linkEwallet yourwaxwallet")
            else:
                await update.message.reply_text("❌ Wrong answer. Try again.")
        except:
            await update.message.reply_text("❌ Please enter a number.")
        return

    elif user_id in verified_users:
        await update.message.reply_text("⚡ Use /plaE or /spacerun to play.")
    else:
        await update.message.reply_text("❗ Start with /lfg to verify first.")

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

    pending_challenges.pop(user_id, None)
    verified_users.add(user_id)

    await update.message.reply_text(f"🔗 Wallet {wallet} linked & verified!

✅ You can now use:
➡️ /plaE to play Emojis Invade
➡️ /spacerun to play Spacerun3008
➡️ /verifyEkey to check NFT key status.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in verified_users:
        await update.message.reply_text("❗ You must /lfg verify first.")
        return

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
        await update.message.reply_text("✅ You own the GK3008 Game Key NFT!")
    else:
        await update.message.reply_text(f"🚫 NFT not found. Buy here:\n{GAME_KEY_DROP_URL}")

async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in verified_users:
        await update.message.reply_text("❗ You must /lfg verify first.")
        return

    async with aiosqlite.connect("botdata.db") as db:
        async with db.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if not result:
        await update.message.reply_text("❌ No wallet linked. Use /linkEwallet.")
        return

    wallet = result[0]
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={REQUIRED_TEMPLATE_ID}&collection_name=games4punks1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if data["data"]:
        await update.message.reply_text(f"🎮 Play Emojis Invade:\n{EMOJIS_INVADE_URL}")
    else:
        await update.message.reply_text(f"🚫 NFT required. Buy here:\n{GAME_KEY_DROP_URL}")

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    players.add(user_id)

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play SPACERUN3008", url=SPACERUN_URL)]]
    )

    await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Game server appears to be online.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_CHAT_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("❌ Please provide a message to broadcast.")
        return
    msg = " ".join(context.args)
    for user_id in players:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
        except:
            continue

async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_CHAT_ID:
        await update.message.reply_text(f"👥 Total players: {len(players)}")

async def message_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_CHAT_ID:
        return
    try:
        user_id = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=msg)
    except:
        await update.message.reply_text("❌ Error sending message.")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    await update.message.reply_text(f"🎉 Welcome {new_member.first_name} to the GKniftyHEADS Channel!")

async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code
    if lang == "en":
        await update.message.reply_text("Welcome to SPACERUN3008!")
    elif lang == "es":
        await update.message.reply_text("¡Bienvenido a SPACERUN3008!")
    else:
        await update.message.reply_text("Language not supported. Defaulting to English.")

@api.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())

async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    async with aiosqlite.connect("botdata.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL)")
        await db.commit()

    app.add_handler(CommandHandler("lfg", lfg))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("message", message_user))
    app.add_handler(CommandHandler("langdetect", detect_language))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ GK3008BOT is running polling...")
    await app.run_polling()

if __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))



