import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import nest_asyncio

# Fix event loop issue for Replit or other environments
nest_asyncio.apply()

# Fetch Bot Token from environment variables (Railway environment variables will be used)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = "https://games4punks.github.io/spacerun3008/"  # Correct URL to the hosted game
GAME_NAME = "spacerun3008"
GAME_TITLE = "Spacerun3008"
GAME_DESCRIPTION = "🎮 Listen & Play to Earn with GK Radio and win WAX NFTs!"
OWNER_CHAT_ID = 1019741898  # Your Telegram user ID

# Track players
players = set()

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# 🎮 Game Command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Learn more about the games and bot.")

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_game(
        chat_id=update.effective_chat.id,
        game_short_name=GAME_NAME,
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play Spacerun3008", url=GAME_URL)]]
    )
    await update.message.reply_text("🎮 Click below to play Spacerun3008:", reply_markup=keyboard)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 Leaderboard: https://stats.uptimerobot.com/z49KWx9Lym")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Game server appears to be online.")

# --- Admin Commands ---
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

async def updateurl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GAME_URL
    if update.effective_user.id == OWNER_CHAT_ID and context.args:
        GAME_URL = context.args[0]
        await update.message.reply_text(f"✅ New game URL set:\n{GAME_URL}")

async def settitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GAME_TITLE
    if update.effective_user.id == OWNER_CHAT_ID:
        GAME_TITLE = " ".join(context.args)
        await update.message.reply_text(f"✅ Title updated to:\n{GAME_TITLE}")

async def setdescription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GAME_DESCRIPTION
    if update.effective_user.id == OWNER_CHAT_ID:
        GAME_DESCRIPTION = " ".join(context.args)
        await update.message.reply_text(f"✅ Description updated.")

# --- New Member Welcome Message ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    lang = new_member.language_code
    welcome_message = f"🎉 Hey {new_member.first_name}, Welcome to the **GKniftyHEADS** Family! 🎮🎉 \n\nWe're excited to have you here! Ready to play and earn WAX NFTs? 🎉\n\nHere are the awesome commands you can use to get started:\n- /spacerun – Dive into the game and start playing!\n- /leaderboard – Check out the latest scores and see how you rank.\n- /about – Find out more about the bot and how it works.\n\nLet’s have some fun! 🚀"
    
    await update.message.reply_text(welcome_message)

# --- Auto Language Detection ---
async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code
    if lang == "en":
        await update.message.reply_text("Welcome to Spacerun3008!")
    elif lang == "es":
        await update.message.reply_text("¡Bienvenido a Spacerun3008!")
    else:
        await update.message.reply_text("Language not supported. Defaulting to English.")

# --- Main ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add commands handlers
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("status", status))

    # Admin Commands
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("message", message_user))
    app.add_handler(CommandHandler("updateurl", updateurl))
    app.add_handler(CommandHandler("settitle", settitle))
    app.add_handler(CommandHandler("setdescription", setdescription))

    # Auto Language Detection
    app.add_handler(CommandHandler("langdetect", detect_language))

    # New Member Welcome
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    print("✅ Bot is running and listening for all commands...")
    await app.run_polling()

import asyncio
asyncio.run(main())















