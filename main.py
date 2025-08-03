import os
import logging
import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL Connection

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Database Functions

def link_wallet_db(telegram_id, wallet):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO linked_wallets (telegram_id, wallet)
                VALUES (%s, %s)
                ON CONFLICT (telegram_id) DO UPDATE SET wallet = EXCLUDED.wallet;
            """, (telegram_id, wallet))
    conn.close()

def unlink_wallet_db(telegram_id):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))
    conn.close()

def is_wallet_linked(telegram_id):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))
            result = cur.fetchone()
    conn.close()
    return result is not None

# Command Handlers

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    lang = user.language_code

    message = (
        "\U0001F525 Welcome to GKniftyHEADS! \U0001F525\n\n"
        "Want to play Web3 GK games & earn FREE NFTs?\n"
        "\nYou need a GK Game Key NFT.\n"
        "\nGrab yours here: https://neftyblocks.com/collection/games4punks1/drops"
    )

    context.bot.send_message(chat_id=chat_id, text=message)

def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if is_wallet_linked(user_id):
        update.message.reply_text("\U0001F3AE GAME SERVER IS LIVE WHAT YOU WAITING FOR")
    else:
        update.message.reply_text(
            "\U0001F4BB Yes GK Games4PUNKS Studio is LIVE, purchase 1 of 3 available Game Key NFTs to play games: https://neftyblocks.com/collection/games4punks1/drops"
        )

def linkEwallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        update.message.reply_text("Please provide your WAX wallet address. Usage: /linkEwallet YOURWALLET")
        return

    wallet = args[0]
    link_wallet_db(user_id, wallet)
    update.message.reply_text(f"Wallet {wallet} linked successfully!")

def unlinkEwallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    unlink_wallet_db(user_id)
    update.message.reply_text("Your wallet has been unlinked.")

def verifyEkey(update: Update, context: CallbackContext):
    # Placeholder: This should call AtomicHub API to verify NFT ownership.
    # Simulated response:
    update.message.reply_text("\U0001F4AA YEP YOU READY FOR HODL WARS ")

def snakerun(update: Update, context: CallbackContext):
    update.message.reply_text("Play Snake Run: https://hodlkong64.github.io/snakerun/")

def emojipunks(update: Update, context: CallbackContext):
    update.message.reply_text("Play Emoji Punks: https://games4punks.github.io/emojisinvade/")

def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, start))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("linkEwallet", linkEwallet))
    dispatcher.add_handler(CommandHandler("unlinkEwallet", unlinkEwallet))
    dispatcher.add_handler(CommandHandler("verifyEkey", verifyEkey))
    dispatcher.add_handler(CommandHandler("snakerun", snakerun))
    dispatcher.add_handler(CommandHandler("emojipunks", emojipunks))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()






