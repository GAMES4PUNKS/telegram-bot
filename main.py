import logging
import os
import sqlite3
import aiohttp
import nest_asyncio
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Apply fix for nested event loops
nest_asyncio.apply()

# ENV vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
GAME_KEY_TEMPLATE_ID = "895159"
ATOMIC_API = "https://wax.api.atomicassets.io/atomicassets/v1/assets"
GAME_URL_EMOJI = "https://games4punks.github.io/emojisinvade/"
GAME_URL_SPACERUN = "https://games4punks.github.io/spacerun3008/"

OWNER_CHAT_ID = 1019741898

# DB setup
db = sqlite3.connect("gkbot.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, wallet TEXT, verified INTEGER DEFAULT 0, plays INTEGER DEFAULT 0)")
db.commit()

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Wallet handlers
def set_wallet(user_id, wallet):
    cur.execute("INSERT OR REPLACE INTO users (user_id, wallet) VALUES (?, ?)", (user_id, wallet))
    db.commit()

def get_wallet(user_id):
    cur.execute("SELECT wallet FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def unlink_wallet(user_id):
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    db.commit()

def set_verified(user_id, wallet):
    cur.execute("UPDATE users SET verified = 1 WHERE user_id = ? AND wallet = ?", (user_id, wallet))
    db.commit()

def is_verified(user_id):
    cur.execute("SELECT verified FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row[0] == 1 if row else False

def increment_play(user_id):
    cur.execute("UPDATE users SET plays = plays + 1 WHERE user_id = ?", (user_id,))
    db.commit()

# Telegram bot commands
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Paste your WAX wallet address:")

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if len(text) == 42 and text.endswith(".wam"):
        set_wallet(user_id, text)
        await update.message.reply_text(f"✅ WAX wallet linked: `{text}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid WAX wallet. Please try again.")

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    unlink_wallet(update.effective_user.id)
    await update.message.reply_text("🧹 Wallet unlinked successfully.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ No wallet linked. Use linkEwallet first.")
        return

    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                set_verified(user_id, wallet)
                await update.message.reply_text(
                    "✅ Game Key NFT verified! You now have full access to Emojis Invade & Spacerun3008."
                )
            else:
                await update.message.reply_text(
                    "❌ No valid Game Key NFT found in your wallet.\n\n"
                    "🔑 *You need the GK3008 Game Key NFT to play both games!*\n"
                    "[👉 Buy it on NeftyBlocks](https://neftyblocks.com/collection/games4punks1/drops/236466)",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

async def plaE(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("❌ You must verify your Game Key NFT first using verifyEkey")
        return
    increment_play(user_id)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play Emojis Invade", url=GAME_URL_EMOJI)]])
    await update.message.reply_text("🎯 Click to play Emojis Invade!", reply_markup=keyboard)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("❌ You must verify your Game Key NFT first using verifyEkey")
        return
    increment_play(user_id)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play SPACERUN3008", url=GAME_URL_SPACERUN)]])
    await update.message.reply_text("🚀 Click to play SPACERUN3008!", reply_markup=keyboard)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Game server appears to be online.")

async def langdetect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code
    if lang == "en":
        await update.message.reply_text("🌍 Language detected: English")
    elif lang == "es":
        await update.message.reply_text("🌍 Idioma detectado: Español")
    else:
        await update.message.reply_text("🌍 Language not fully supported. Defaulting to English.")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    welcome_message = (
        f"🎉 *Welcome to the GKniftyHEADS Gaming Zone, {new_member.first_name}!* 🎮\n\n"
        f"You’ve just stepped into the world of *SPACERUN3008* and *EMOJIS INVADE* — two exclusive HTML5 games powered by Web3 and the WAX blockchain.\n\n"
        f"🚀 *How to Play & Earn:*\n"
        f"1. linkEwallet – Link your WAX wallet\n"
        f"2. verifyEkey – Verify your Game Key NFT\n"
        f"3. plaE – Play Emojis Invade (NFT required)\n"
        f"4. spacerun – Play Spacerun3008 (NFT required)\n\n"
        f"🔑 *Don’t have the Game Key NFT yet?*\n"
        f"[👉 Buy one here](https://neftyblocks.com/collection/games4punks1/drops/236466)\n\n"
        f"💬 Win NFTs. Climb the leaderboard. Become a legend.\n"
        f"Let’s go, soldier. 🎮🔥"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown", disable_web_page_preview=True)

# FastAPI for external game integrations
api = FastAPI()

@api.get("/verify")
def api_verify(wallet: str):
    query = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async def check():
        async with aiohttp.ClientSession() as session:
            async with session.get(query) as res:
                r = await res.json()
                return bool(r.get("data"))
    result = asyncio.run(check())
    return {"wallet": wallet, "verified": result}

@api.get("/stats")
def api_stats(user_id: int):
    cur.execute("SELECT plays FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return {"user_id": user_id, "plays": row[0] if row else 0}

# Launch both bot + API
async def launch_all():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", plaE))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("langdetect", langdetect))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    print("✅ GK3008bot is running with FastAPI")
    await app.start()
    await app.updater.start_polling()

# Run bot and FastAPI app together
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(launch_all())
    uvicorn.run(api, host="0.0.0.0", port=8000)
        conn.execute("CREATE TABLE IF NOT EXISTS linked_wallets (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS verified_users (telegram_id INTEGER PRIMARY KEY, wallet TEXT NOT NULL, verified INTEGER DEFAULT 0)")

def link_wallet(telegram_id: int, wallet: str):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("REPLACE INTO linked_wallets (telegram_id, wallet) VALUES (?, ?)", (telegram_id, wallet))

def get_wallet(telegram_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = ?", (telegram_id,)).fetchone()
        return result[0] if result else None

def unlink_wallet(telegram_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM linked_wallets WHERE telegram_id = ?", (telegram_id,))

def set_verified(telegram_id: int, wallet: str):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO verified_users (telegram_id, wallet, verified)
            VALUES (?, ?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET verified = 1, wallet = ?
        """, (telegram_id, wallet))

def is_wallet_verified(wallet: str):
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute("SELECT verified FROM verified_users WHERE wallet = ? AND verified = 1", (wallet,)).fetchone()
        return bool(result)

# === COMMANDS ===
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧾 Send your WAX wallet (e.g., abcd.wam):")
    return 1

async def save_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    if wallet.endswith(".wam") and len(wallet) <= 15 and wallet.replace('.', '').isalnum():
        link_wallet(update.effective_user.id, wallet)
        await update.message.reply_text(f"✅ WAX wallet `{wallet}` linked!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid wallet format. Try again.")
    return ConversationHandler.END

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_wallet(user_id):
        unlink_wallet(user_id)
        await update.message.reply_text("❎ Your WAX wallet has been unlinked.")
    else:
        await update.message.reply_text("⚠️ No wallet is currently linked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ No wallet linked. Use /linkEwallet first.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                set_verified(user_id, wallet)
                await update.message.reply_text("✅ Game Key NFT verified! You now have full access to Emojis Invade & Spacerun3008.")
            else:
                await update.message.reply_text(
                    "❌ No valid Game Key NFT found in your wallet.\n\n"
                    "🔑 *You need the GK3008 Game Key NFT to play both games!*\n"
                    "[👉 Buy it on NeftyBlocks](https://neftyblocks.com/collection/games4punks1/drops/236466)",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

async def play_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link your WAX wallet using /linkEwallet.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                await update.message.reply_text(f"🎮 [▶ Play Emojis Invade]({EMOJI_GAME_URL})", parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await update.message.reply_text(
                    f"❌ You don’t own the Game Key NFT.\n[Buy it on NeftyBlocks]({TEMPLATE_LINK})",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link your WAX wallet using /linkEwallet.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play SPACERUN3008", url=SPACERUN_GAME_URL)]])
                await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy it on NeftyBlocks:\n{TEMPLATE_LINK}")

# === UTILS ===
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    msg = (
        f"🎉 *Welcome to the GKniftyHEADS Gaming Zone, {new_member.first_name}!* 🎮\n\n"
        f"You’ve just stepped into the world of *SPACERUN3008* and *EMOJIS INVADE* — two exclusive HTML5 games powered by Web3 and the WAX blockchain.\n\n"
        f"🚀 *Here’s how to start playing & earning:*\n"
        f"1. `/linkEwallet` – Link your WAX wallet\n"
        f"2. `/verifyEkey` – Verify you own the *GK3008 Game Key NFT*\n"
        f"3. `/plaE` – Play *EMOJIS INVADE* (NFT required)\n"
        f"4. `/spacerun` – Play *SPACERUN3008* (NFT required)\n\n"
        f"🔑 *Don’t have the NFT yet?*\n"
        f"[👉 Buy it on NeftyBlocks]({TEMPLATE_LINK})\n\n"
        f"💬 Stay active, win WAX NFTs, and dominate the leaderboard.\n"
        f"Welcome to the rebellion. This ain’t just a game — it’s a takeover. 🎮🔥"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code
    if lang == "en":
        await update.message.reply_text("Welcome to SPACERUN3008!")
    elif lang == "es":
        await update.message.reply_text("¡Bienvenido a SPACERUN3008!")
    else:
        await update.message.reply_text("Language not supported. Defaulting to English.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Game server appears to be online.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_CHAT_ID:
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

# === FASTAPI ===
api = FastAPI()
api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@api.get("/verify-wallet")
def verify_wallet(wallet: str = Query(...)):
    return {
        "status": "ok" if is_wallet_verified(wallet) else "error",
        "verified": is_wallet_verified(wallet),
        "reason": None if is_wallet_verified(wallet) else "Wallet not verified via Telegram bot with Game Key."
    }

def start_api():
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

# === MAIN ===
async def run_bot():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("plaE", play_emoji))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("message", message_user))
    app.add_handler(CommandHandler("langdetect", detect_language))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("linkEwallet", link_ewallet)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_wallet)]},
        fallbacks=[]
    ))
    print("✅ Telegram bot is live...")
    await app.run_polling()

if __name__ == "__main__":
    Thread(target=start_api).start()
    asyncio.run(run_bot())
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

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link your WAX wallet using /linkEwallet.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play SPACERUN3008", url=SPACERUN_GAME_URL)]])
                await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy it here:\n{TEMPLATE_LINK}")

async def play_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link your WAX wallet using /linkEwallet.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                await update.message.reply_text(f"🎮 [▶ Play Emojis Invade]({EMOJI_GAME_URL})", parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy one:\n{TEMPLATE_LINK}")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ No wallet linked. Use /linkEwallet first.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                set_verified(user_id, wallet)
                await update.message.reply_text("✅ Your Game Key NFT is verified. You now have access to all games.")
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy one here:\n{TEMPLATE_LINK}")

async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧾 Send your WAX wallet (e.g., abcd.wam):")
    return 1

async def save_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    if wallet.endswith(".wam") and len(wallet) <= 15 and wallet.replace('.', '').isalnum():
        link_wallet(update.effective_user.id, wallet)
        await update.message.reply_text(f"✅ WAX wallet `{wallet}` linked!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid wallet format. Try again.")
    return ConversationHandler.END

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_wallet(user_id):
        unlink_wallet(user_id)
        await update.message.reply_text("❎ Your WAX wallet has been unlinked.")
    else:
        await update.message.reply_text("⚠️ No wallet is currently linked.")

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
    welcome_message = (
        f"🎉 Welcome {new_member.first_name} to the **GKniftyHEADS** Channel! 🎮\n\n"
        f"Play our featured game SPACERUN3008 and win WAX NFTs!\n\n"
        f"Here’s what you can do:\n"
        f"- Use /spacerun to play the game.\n"
        f"- Use /status to check the game status.\n"
        f"- Use /about to learn more about the bot and game. (Links in future updates.)\n\n"
        f"Let’s have some fun! 🚀"
    )
    await update.message.reply_text(welcome_message)

async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code
    if lang == "en":
        await update.message.reply_text("Welcome to SPACERUN3008!")
    elif lang == "es":
        await update.message.reply_text("¡Bienvenido a SPACERUN3008!")
    else:
        await update.message.reply_text("Language not supported. Defaulting to English.")

api = FastAPI()
api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@api.get("/verify-wallet")
def verify_wallet(wallet: str = Query(...)):
    return {
        "status": "ok" if is_wallet_verified(wallet) else "error",
        "verified": is_wallet_verified(wallet),
        "reason": None if is_wallet_verified(wallet) else "Wallet not verified via Telegram bot with Game Key."
    }

def start_api():
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

async def run_bot():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("plaE", play_emoji))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("message", message_user))
    app.add_handler(CommandHandler("langdetect", detect_language))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("linkEwallet", link_ewallet)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_wallet)]},
        fallbacks=[]
    ))
    print("✅ Telegram bot is live...")
    await app.run_polling()

if __name__ == "__main__":
    Thread(target=start_api).start()
    asyncio.run(run_bot())

