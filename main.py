import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Fetch Bot Token from Heroku environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Command handler for '/lfg'
async def lfg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Create the inline keyboard for the button to start the game
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play SPACERUN3008", url="https://t.me/GAMES4PUNKSBOT?game=SPACERUN3008")]]
    )
    await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)

# Main function to run the bot
async def main():
    # Build the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handler
    application.add_handler(CommandHandler("lfg", lfg))

    logger.info("Bot is running and listening for commands...")
    # This will internally handle the event loop and polling
    await application.run_polling()

# This part is to ensure that the bot starts properly
if __name__ == "__main__":
    # Directly run the async main function using the application lifecycle manager
    import asyncio
    asyncio.run(main())











