import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import nest_asyncio
import os

# Enable nested event loop (Render compatibility)
nest_asyncio.apply()

# BOT TOKEN from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Check for token existence
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Command Handlers
def start(update, context):
    update.message.reply_text("Welcome to GAMES4PUNKS BOT!")

def status(update, context):
    update.message.reply_text("GK Games4PUNKS Studio is LIVE, purchase a Game Key NFT to play: https://neftyblocks.com/collection/games4punks1/drops")

# Error handler
def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal (Ctrl+C)
    updater.idle()

if __name__ == '__main__':
    main()





