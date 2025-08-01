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
        raise HTTPException(status_code=403, detail="Unauthorized")

async def send_math_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a, b = random.randint(1, 10), random.randint(1, 10)
    answer = a + b
    context.user_data["captcha_answer"] = answer
    await update.message.reply_text(f"🤖 CAPTCHA: What is {a} + {b}?")

async def verify_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "captcha_answer" in context.user_data:
        try:
            if int(update.message.text) == context.user_data["captcha_answer"]:
                del context.user_data["captcha_answer"]
                await update.message.reply_text("✅ Verified! You may now use the bot.")
            else:
                await send_math_captcha(update, context)
        except:
            await send_math_captcha(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_math_captcha(update, context)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("❌ You must verify your NFT to play. Use /verifyEkey.")
        return
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play Spacerun3008", url=GAME_URL_SPACERUN)]]
    )
    await update.message.reply_text("🎮 Click below to play Spacerun3008:", reply_markup=keyboard)

async def plae(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_verified(user_id):
        await update.message.reply_text("❌ You must verify your NFT to play. Use /verifyEkey.")
        return
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play Emojis Invade", url=GAME_URL_EMOJI)]]
    )
    await update.message.reply_text("🎮 Click below to play Emojis Invade:", reply_markup=keyboard)

def link_wallet(user_id: int, wallet: str):
    cur.execute("INSERT OR REPLACE INTO users (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
    conn.commit()

def unlink_wallet(user_id: int):
    cur.execute("UPDATE users SET wallet=NULL, verified=0 WHERE telegram_id=?", (user_id,))
    conn.commit()

def get_wallet(user_id: int):
    cur.execute("SELECT wallet FROM users WHERE telegram_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def set_verified(user_id: int):
    cur.execute("UPDATE users SET verified=1 WHERE telegram_id=?", (user_id,))
    conn.commit()

def is_verified(user_id: int):
    cur.execute("SELECT verified FROM users WHERE telegram_id=?", (user_id,))
    row = cur.fetchone()
    return row and row[0] == 1

async def has_game_key(wallet: str):
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?collection_name=games4punks1&template_id={GAME_KEY_TEMPLATE_ID}&owner={wallet}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return len(data.get("data", [])) > 0

async def linkewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 Please send your WAX wallet address:")
    context.user_data["awaiting_wallet"] = True

async def handle_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_wallet"):
        wallet = update.message.text.strip()
        if not wallet.startswith("wax") or len(wallet) != 12:
            await update.message.reply_text("❌ Invalid WAX address. Must start with 'wax' and be 12 characters.")
            return
        link_wallet(update.effective_user.id, wallet)
        context.user_data["awaiting_wallet"] = False
        await update.message.reply_text("✅ Wallet linked. Now use /verifyEkey")

async def verifyekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ Please link your wallet first using /linkEwallet")
        return
    if await has_game_key(wallet):
        set_verified(user_id)
        await update.message.reply_text("✅ You hold a valid Game Key NFT! Access granted.")
    else:
        await update.message.reply_text("❌ No valid Game Key NFT found. You can get one at https://neftyblocks.com/collection/games4punks1/drops/236466")

async def unlinkewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    unlink_wallet(update.effective_user.id)
    await update.message.reply_text("🗑️ Wallet unlinked and verification reset.")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = f"""
🎉 Welcome {name} to the GKniftyHEADS Channel! 🎮

🔑 To play our games, you’ll need a verified Game Key NFT.

🎮 /spacerun – Play Spacerun3008
👾 /plaE – Play Emojis Invade

👉 Use /linkEwallet to link your WAX wallet
👉 Use /verifyEkey to verify you own a Game Key NFT

🛒 Buy Game Key NFT:
https://neftyblocks.com/collection/games4punks1/drops/236466
"""
    await update.message.reply_text(msg)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("linkEwallet", linkewallet))
app.add_handler(CommandHandler("verifyEkey", verifyekey))
app.add_handler(CommandHandler("unlinkEwallet", unlinkewallet))
app.add_handler(CommandHandler("spacerun", spacerun))
app.add_handler(CommandHandler("plaE", plae))
app.add_handler(CommandHandler("welcome", welcome))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), verify_captcha))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_wallet_input))

print("✅ Bot running...")

from threading import Thread
import uvicorn

api = FastAPI()

@api.get("/api/wallet/{telegram_id}")
def api_wallet(telegram_id: int, request: Request):
    verify_api_key(request)
    wallet = get_wallet(telegram_id)
    return {"wallet": wallet or ""}

@api.get("/api/verified/{telegram_id}")
async def api_verified(telegram_id: int, request: Request):
    verify_api_key(request)
    wallet = get_wallet(telegram_id)
    if not wallet:
        return {"verified": False}
    return {"verified": await has_game_key(wallet)}

def run_fastapi():
    uvicorn.run(api, host="0.0.0.0", port=8000)

Thread(target=run_fastapi).start()

import asyncio
asyncio.run(app.run_polling())
logging.basicConfig(level=logging.INFO)

# === CAPTCHA CACHE ===
pending_captchas = {}

# === FASTAPI SERVER ===
api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/api/wallet/{telegram_id}")
def get_wallet_api(telegram_id: int):
    cur.execute("SELECT wallet FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    return {"wallet": row[0] if row else ""}

@api.get("/api/verified/{telegram_id}")
async def get_verified_api(telegram_id: int):
    cur.execute("SELECT wallet FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    if not row:
        return {"verified": False}
    wallet = row[0]
    async with aiohttp.ClientSession() as session:
        async with session.get(GAMEKEY_TEMPLATE_URL + wallet) as resp:
            data = await resp.json()
            return {"verified": data.get("data", []) != []}

# === HELPERS ===
async def has_game_key(wallet: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.get(GAMEKEY_TEMPLATE_URL + wallet) as resp:
            data = await resp.json()
            return bool(data.get("data"))

def get_wallet(telegram_id: int) -> str:
    cur.execute("SELECT wallet FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    return row[0] if row else None

# === COMMANDS ===
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in pending_captchas:
        await update.message.reply_text("❗ You already have a pending CAPTCHA.")
        return

    a, b = random.randint(1, 9), random.randint(1, 9)
    pending_captchas[user_id] = (a + b)
    await update.message.reply_text(f"🧠 To link your wallet, solve this: {a} + {b} = ?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pending_captchas:
        return

    try:
        answer = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Please send a number.")
        return

    if answer == pending_captchas[user_id]:
        del pending_captchas[user_id]
        await update.message.reply_text("✅ Correct! Now send your WAX wallet address.")
        context.user_data["awaiting_wallet"] = True
    elif "awaiting_wallet" in context.user_data:
        wallet = update.message.text.strip()
        cur.execute("REPLACE INTO users (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
        conn.commit()
        await update.message.reply_text(f"✅ Wallet linked: `{wallet}`", parse_mode="Markdown")
        context.user_data.pop("awaiting_wallet", None)
    else:
        await update.message.reply_text("❌ Incorrect. Try /linkEwallet again.")
        del pending_captchas[user_id]

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cur.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
    conn.commit()
    await update.message.reply_text("🔓 Wallet unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link a wallet first with /linkEwallet.")
        return
    if await has_game_key(wallet):
        await update.message.reply_text("✅ You own the required NFT game key.")
    else:
        await update.message.reply_text("❌ No valid NFT found.\n🎟️ Buy one at: https://neftyblocks.com/collection/games4punks1/drops/236466")

async def play_emojis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ Link wallet first with /linkEwallet.")
        return
    if not await has_game_key(wallet):
        await update.message.reply_text("❌ NFT game key not detected.")
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play Emojis Invade", url=EMOJIS_URL)]])
    await update.message.reply_text("🕹️ Click to play Emojis Invade!", reply_markup=keyboard)

async def play_spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ Link wallet first with /linkEwallet.")
        return
    if not await has_game_key(wallet):
        await update.message.reply_text("❌ NFT game key not detected.")
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Play SPACERUN3008", url=SPACERUN_URL)]])
    await update.message.reply_text("🚀 Click to play SPACERUN3008!", reply_markup=keyboard)

# === WELCOME MESSAGE ===
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Welcome {name}!\n\n"
        "🎮 Play & Earn:\n"
        "▶️ /plaE – Emojis Invade\n"
        "🚀 /spacerun – SPACERUN3008\n\n"
        "💳 You need an NFT key to play:\n"
        "🎟️ https://neftyblocks.com/collection/games4punks1/drops/236466\n\n"
        "🔗 Link your wallet:\n"
        "/linkEwallet\n"
        "✅ Check your key:\n"
        "/verifyEkey"
    )

# === MAIN LAUNCH ===
async def telegram_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", welcome))
    app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", play_emojis))
    app.add_handler(CommandHandler("spacerun", play_spacerun))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ GK3008BOT is online.")
    await app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: uvicorn.run(api, host="0.0.0.0", port=8000)).start()
    asyncio.run(telegram_bot())
    allow_headers=["*"],
)

@api.get("/api/wallet/{telegram_id}")
def get_wallet_api(telegram_id: int):
    wallet = get_wallet(telegram_id)
    return {"wallet": wallet or ""}

@api.get("/api/verified/{telegram_id}")
async def get_verified_api(telegram_id: int):
    wallet = get_wallet(telegram_id)
    if not wallet:
        return {"verified": False}
    result = await has_game_key(wallet)
    return {"verified": result}

# === WAX NFT CHECK ===
async def has_game_key(wallet: str) -> bool:
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?collection_name=games4punks1&template_id={GAME_KEY_TEMPLATE}&owner={wallet}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get("data", []) != []

# === DATABASE HELPERS ===
def set_wallet(user_id, wallet):
    cur.execute("INSERT OR REPLACE INTO users (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
    conn.commit()

def get_wallet(user_id):
    cur.execute("SELECT wallet FROM users WHERE telegram_id = ?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def unlink_wallet(user_id):
    cur.execute("UPDATE users SET wallet = NULL WHERE telegram_id = ?", (user_id,))
    conn.commit()

# === CAPTCHA STATE ===
captcha_answers = {}

# === COMMANDS ===
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a, b = random.randint(1, 10), random.randint(1, 10)
    captcha_answers[user_id] = a + b
    await update.message.reply_text(f"🧠 Answer this to prove you're human: What is {a} + {b}?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in captcha_answers:
        try:
            answer = int(update.message.text.strip())
            if answer == captcha_answers[user_id]:
                del captcha_answers[user_id]
                await update.message.reply_text("✅ Great. Now send your WAX wallet address:")
            else:
                await update.message.reply_text("❌ Incorrect. Try again using /linkEwallet.")
        except ValueError:
            await update.message.reply_text("❌ Numbers only. Try again.")
        return
    if update.message.text.startswith("wax."):
        set_wallet(user_id, update.message.text.strip())
        await update.message.reply_text("🔗 Wallet linked successfully.")
    else:
        await update.message.reply_text("⚠️ Unrecognized input. Use commands or send WAX address after verification.")

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    unlink_wallet(user_id)
    await update.message.reply_text("❌ Your wallet has been unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("⚠️ You must link your wallet first using /linkEwallet")
        return
    if await has_game_key(wallet):
        cur.execute("UPDATE users SET verified = 1 WHERE telegram_id = ?", (user_id,))
        conn.commit()
        await update.message.reply_text("✅ Game Key verified. You're ready to play!")
    else:
        await update.message.reply_text("❌ No Game Key NFT found.\n🎟️ Buy one: https://neftyblocks.com/collection/games4punks1/drops/236466")

async def play_emojis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet or not await has_game_key(wallet):
        await update.message.reply_text("🚫 Access denied. Use /verifyEkey first.")
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play Emojis Invade", url=GAME_URL_EMOJIS)]])
    await update.message.reply_text("🎮 Click to play Emojis Invade:", reply_markup=keyboard)

async def play_spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet or not await has_game_key(wallet):
        await update.message.reply_text("🚫 Access denied. Use /verifyEkey first.")
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play Spacerun3008", url=GAME_URL_SPACERUN)]])
    await update.message.reply_text("🎮 Click to play Spacerun3008:", reply_markup=keyboard)

# === TELEGRAM BOT ===
async def telegram_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", play_emojis))
    app.add_handler(CommandHandler("spacerun", play_spacerun))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ GK3008BOT is running...")
    await app.run_polling()

# === LAUNCH BOTH ===
if __name__ == "__main__":
    def start_api():
        uvicorn.run(api, host="0.0.0.0", port=8000)

    threading.Thread(target=start_api).start()
    asyncio.run(telegram_bot())
captcha_sessions = {}

# === Utility Functions ===
def set_wallet(user_id, wallet):
    cur.execute("INSERT OR REPLACE INTO users (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
    conn.commit()

def get_wallet(user_id):
    cur.execute("SELECT wallet FROM users WHERE telegram_id = ?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def remove_wallet(user_id):
    cur.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
    conn.commit()

def has_game_key_nft(wallet):
    async def fetch():
        async with aiohttp.ClientSession() as session:
            async with session.get(ATOMIC_TEMPLATE_URL + wallet) as resp:
                data = await resp.json()
                return len(data.get("data", [])) > 0
    return fetch()

# === Bot Command Handlers ===
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a, b = random.randint(1, 9), random.randint(1, 9)
    captcha_sessions[user_id] = a + b
    await update.message.reply_text(f"🤖 CAPTCHA Check: What is {a} + {b}?")

async def handle_wallet_or_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in captcha_sessions:
        try:
            if int(text) == captcha_sessions[user_id]:
                del captcha_sessions[user_id]
                await update.message.reply_text("✅ Human verified. Now send your WAX wallet address:")
            else:
                await update.message.reply_text("❌ CAPTCHA failed. Try /linkEwallet again.")
            return
        except:
            await update.message.reply_text("❌ Please enter a number.")
            return

    if len(text) == 42 and text.endswith(".wam"):
        set_wallet(user_id, text)
        await update.message.reply_text(f"✅ WAX wallet linked: `{text}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid WAX wallet. Try again.")

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    remove_wallet(user_id)
    await update.message.reply_text("🚫 Wallet unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You need to /linkEwallet first.")
        return
    has_nft = await has_game_key_nft(wallet)
    if has_nft:
        await update.message.reply_text("✅ Game Key NFT verified! You may now /plaE or /spacerun.")
    else:
        await update.message.reply_text(
            "❌ No valid Game Key NFT found.\n"
            "🔑 *You need the GK3008 Game Key NFT to play.*\n"
            "[Buy one here](https://neftyblocks.com/collection/games4punks1/drops/236466)",
            parse_mode="Markdown", disable_web_page_preview=True
        )

async def play_emojis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You need to /linkEwallet first.")
        return
    has_nft = await has_game_key_nft(wallet)
    if has_nft:
        button = InlineKeyboardButton("▶️ Play Emojis Invade", url=EMOJIS_GAME_URL)
        await update.message.reply_text("🎮 Click to play Emojis Invade:", reply_markup=InlineKeyboardMarkup([[button]]))
    else:
        await update.message.reply_text("❌ Access denied. NFT not found. Use /verifyEkey.")

async def play_spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You need to /linkEwallet first.")
        return
    has_nft = await has_game_key_nft(wallet)
    if has_nft:
        button = InlineKeyboardButton("▶️ Play Spacerun3008", url=SPACERUN_GAME_URL)
        await update.message.reply_text("🎮 Click to play Spacerun3008:", reply_markup=InlineKeyboardMarkup([[button]]))
    else:
        await update.message.reply_text("❌ Access denied. NFT not found. Use /verifyEkey.")

# === Main App ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", play_emojis))
    app.add_handler(CommandHandler("spacerun", play_spacerun))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_or_captcha))

    print("✅ GK3008 Bot is live...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

# Utils
def set_wallet(user_id, wallet):
    cur.execute("INSERT OR REPLACE INTO users (telegram_id, wallet) VALUES (?, ?)", (user_id, wallet))
    conn.commit()

def get_wallet(user_id):
    cur.execute("SELECT wallet FROM users WHERE telegram_id = ?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def remove_wallet(user_id):
    cur.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
    conn.commit()

def has_game_key_nft(wallet):
    async def fetch():
        async with aiohttp.ClientSession() as session:
            async with session.get(ATOMIC_TEMPLATE_URL + wallet) as resp:
                data = await resp.json()
                return len(data.get("data", [])) > 0
    return fetch()

# Commands
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    a, b = random.randint(1, 9), random.randint(1, 9)
    captcha_sessions[user_id] = a + b
    await update.message.reply_text(f"🤖 CAPTCHA Check: What is {a} + {b}?")

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # CAPTCHA check
    if user_id in captcha_sessions:
        try:
            if int(text) == captcha_sessions[user_id]:
                del captcha_sessions[user_id]
                await update.message.reply_text("✅ Human verified. Now send your WAX wallet address:")
            else:
                await update.message.reply_text("❌ CAPTCHA failed. Try /linkEwallet again.")
            return
        except:
            await update.message.reply_text("❌ Please enter a number.")
            return

    if len(text) == 42 and text.endswith(".wam"):
        set_wallet(user_id, text)
        await update.message.reply_text(f"✅ WAX wallet linked: `{text}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid WAX wallet. Try again.")

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    remove_wallet(user_id)
    await update.message.reply_text("🚫 Wallet unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You need to /linkEwallet first.")
        return
    has_nft = await has_game_key_nft(wallet)
    if has_nft:
        await update.message.reply_text("✅ Game Key NFT verified! You may now /plaE or /spacerun.")
    else:
        await update.message.reply_text(
            "❌ No valid Game Key NFT found.\n"
            "🔑 *You need the GK3008 Game Key NFT to play.*\n"
            "[Buy one here](https://neftyblocks.com/collection/games4punks1/drops/236466)",
            parse_mode="Markdown", disable_web_page_preview=True
        )

async def play_emojis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You need to /linkEwallet first.")
        return
    has_nft = await has_game_key_nft(wallet)
    if has_nft:
        button = InlineKeyboardButton("▶️ Play Emojis Invade", url=EMOJIS_GAME_URL)
        await update.message.reply_text("🎮 Click to play Emojis Invade:", reply_markup=InlineKeyboardMarkup([[button]]))
    else:
        await update.message.reply_text("❌ Access denied. NFT not found. Use /verifyEkey.")

async def play_spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You need to /linkEwallet first.")
        return
    has_nft = await has_game_key_nft(wallet)
    if has_nft:
        button = InlineKeyboardButton("▶️ Play Spacerun3008", url=SPACERUN_GAME_URL)
        await update.message.reply_text("🎮 Click to play Spacerun3008:", reply_markup=InlineKeyboardMarkup([[button]]))
    else:
        await update.message.reply_text("❌ Access denied. NFT not found. Use /verifyEkey.")

# Launch
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("plaE", play_emojis))
    app.add_handler(CommandHandler("spacerun", play_spacerun))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))

    print("✅ GK3008 Bot is live...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
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

