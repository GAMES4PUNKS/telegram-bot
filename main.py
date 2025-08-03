import logging
import os
import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=5432
    )

# Command Handlers
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome to GK Games4PUNKS Bot!")

def status(update: Update, context: CallbackContext) -> None:
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT verified FROM verified_users WHERE telegram_id = %s", (telegram_id,))
    result = cur.fetchone()

    if result and result[0]:
        update.message.reply_text("GAME SERVER IS LIVE WHAT YOU WAITING FOR")
    else:
        update.message.reply_text("Yes GK Games4PUNKS Studio is LIVE, purchase a Game Key NFT to play games: https://neftyblocks.com/collection/games4punks1/drops")

    cur.close()
    conn.close()

def link_ewallet(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Usage: /linkEwallet <your_wallet_address>")
        return

    wallet = context.args[0]
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO linked_wallets (telegram_id, wallet) VALUES (%s, %s) ON CONFLICT (telegram_id) DO UPDATE SET wallet = %s", (telegram_id, wallet, wallet))
    conn.commit()

    update.message.reply_text(f"Wallet {wallet} linked successfully!")

    cur.close()
    conn.close()

def unlink_ewallet(update: Update, context: CallbackContext) -> None:
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))
    conn.commit()

    update.message.reply_text("Your wallet has been unlinked.")

    cur.close()
    conn.close()

def verify_ekey(update: Update, context: CallbackContext) -> None:
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE verified_users SET verified = TRUE WHERE telegram_id = %s", (telegram_id,))
    conn.commit()

    update.message.reply_text("YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")

    cur.close()
    conn.close()

def snakerun(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Play SnakeRun: https://hodlkong64.github.io/snakerun/")

def emojipunks(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Play EmojiPunks: https://games4punks.github.io/emojisinvade/")

def welcome_new_member(update: Update, context: CallbackContext) -> None:
    for member in update.message.new_chat_members:
        update.message.reply_text(
            f"Welcome {member.full_name}! To play Web3 GK games & earn FREE NFTs, own a GK Game Key NFT: https://neftyblocks.com/collection/games4punks1/drops"
        )

def main():
    updater = Updater(os.getenv("BOT_TOKEN"), use_context=True)
    dp = updater.dispatcher

    # Command Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("linkEwallet", link_ewallet))
    dp.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    dp.add_handler(CommandHandler("verifyEkey", verify_ekey))
    dp.add_handler(CommandHandler("snakerun", snakerun))
    dp.add_handler(CommandHandler("emojipunks", emojipunks))

    # Welcome Handler
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_member))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()






