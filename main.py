import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

# Fix event loop issue for Replit
nest_asyncio.apply()

# Fetch Bot Token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GAME_URL = "https://t.me/GAMES4PUNKSBOT?game=SPACERUN3008"  # Game URL for SPACERUN3008
GAME_NAME = "SPACERUN3008"  # Game Short Name

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# --- Command Handlers ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Use /lfg to play SPACERUN3008\n📊 /leaderboard for scores"
    )

async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send the game URL to the user
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play SPACERUN3008", url=GAME_URL)]]
    )
    await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)

# --- Main Bot Setup ---
async def main():
    # Set up the application and handlers
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lfg", lfg))

    print("✅ Bot is running and listening for commands...")
    await app.run_polling()

import asyncio
asyncio.run(main())



