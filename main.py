import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import nest_asyncio

nest_asyncio.apply()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables!")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text("Welcome to GAMES4PUNKS BOT!")

def status(update, context):
    update.message.reply_text("GK Games4PUNKS Studio is LIVE, purchase a Game Key NFT to play: https://neftyblocks.com/collection/games4punks1/drops")

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
