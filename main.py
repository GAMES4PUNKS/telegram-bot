import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import nest_asyncio

# Fix event loop issue for environments like Replit
nest_asyncio.apply()

# Bot token from Railway or GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Game details
GAME_URL = "https://games4punks.github.io/spacerun3008/"
GAME_NAME = "SPACERUN3008"
GAME_TITLE = "Spacerun3008"
GAME_DESCRIPTION = " Listen, Play & Earn with GK Radio and win WAX NFTs!"

# Static pages hosted on GitHub Pages (retaining links for future reference)
ABOUT_URL = "https://games4punks.github.io/spacerun3008/about.html"
LEADERBOARD_URL = "https://games4punks.github.io/spacerun3008/leaderboard.html"

# Bot owner ID
OWNER_CHAT_ID = 1019741898

# Track players
players = set()

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Game launch command
async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_game(
        chat_id=update.effective_chat.id,
        game_short_name=GAME_NAME,
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(" Play SPACERUN3008", url=GAME_URL)]]
    )
    await update.message.reply_text(" Click below to play SPACERUN3008:", reply_markup=keyboard)

# Game status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(" Game server appears to be online.")

# Admin: broadcast message
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_CHAT_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text(" Please provide a message to broadcast.")
        return
    msg = " ".join(context.args)
    for user_id in players:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
        except:
            continue

# Admin: list players
async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_CHAT_ID:
        await update.message.reply_text(f" Total players: {len(players)}")

# Admin: send direct message
async def message_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_CHAT_ID:
        return
    try:
        user_id = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=msg)
    except:
        await update.message.reply_text(" Error sending message.")

# New member welcome
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    welcome_message = (
        f" Welcome {new_member.first_name} to the **GKniftyHEADS** Channel! \n\n"
        f"Play our featured game SPACERUN3008 and win WAX NFTs!\n\n"
        f"Here’s what you can do:\n"
        f"- Use /spacerun to play the game.\n"
        f"- Use /status to check the game status.\n"
        f"- Use /about to learn more about the bot and game. (Links in future updates.)\n\n"
        f"Let’s have some fun! "
    )
    await update.message.reply_text(welcome_message)

# Language auto-detection
async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code
    if lang == "en":
        await update.message.reply_text("Welcome to SPACERUN3008!")
    elif lang == "es":
        await update.message.reply_text("¡Bienvenido a SPACERUN3008!")
    else:
        await update.message.reply_text("Language not supported. Defaulting to English.")

# Main app launch
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Public Commands
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("status", status))

    # Admin Commands
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("message", message_user))

    # Extras
    app.add_handler(CommandHandler("langdetect", detect_language))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    print(" Bot is running and listening for all commands...")
    await app.run_polling()

# Start the bot
import asyncio
asyncio.run(main())











