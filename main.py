from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import Dispatcher, Updater

import os

# Your bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
HEROKU_URL = "https://your-heroku-app-url.herokuapp.com"  # Replace with your Heroku app's URL
BOT_URL = f"{HEROKU_URL}/{BOT_TOKEN}"

async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send the game link to the user
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play SPACERUN3008", url="https://t.me/GAMES4PUNKSBOT?game=SPACERUN3008")]]
    )
    await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Set webhook instead of polling
    await app.bot.set_webhook(url=BOT_URL)

    # Add command handler
    app.add_handler(CommandHandler("lfg", lfg))

    print("✅ Bot is running and listening for commands...")
    await app.run_webhook()

import asyncio
asyncio.run(main())




