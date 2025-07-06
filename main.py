import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Command handler for /start
async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf'Hello {user.mention_html()}! Welcome to the SPACERUN3008 game bot!',
    )

# Command handler for the game link
async def spacerun(update: Update, context):
    await update.message.reply_text(
        "Click here to play SPACERUN3008: t.me/GAMES4PUNKSBOT?game=SPACERUN3008"
    )

# Main function to run the bot
async def main():
    bot_token = os.getenv('BOT_TOKEN')  # Get the bot token from environment variables
    application = ApplicationBuilder().token(bot_token).build()

    # Adding command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spacerun", spacerun))

    # Start the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())