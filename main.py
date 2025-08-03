import os
import asyncio
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ChatMemberHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

GAME_KEY_TEMPLATES = [
    "898303",  # GAME-KEY-ROYALE
    "895159",  # GK3008-Game-Key
    "898306"   # GAME-KEY-BATTLE-ROYALE
]

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo! I'm GK Games Bot — type /status to check server!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT wallet FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))
        wallet = cur.fetchone()

    # Simulate AtomicHub API check (replace with actual WAX query)
    owns_game_key = False  # Default False, replace with real API logic.
    if wallet:
        # Example: add your API ownership logic here.
        owns_game_key = True  # TEMP: Assume wallet is valid for now.

    if owns_game_key:
        await update.message.reply_text("GAME SERVER IS LIVE WHAT YOU WAITING FOR")
    else:
        await update.message.reply_text("Yes GK Games4PUNKS Studio is LIVE, purchase 1 of 3 available Game Key NFTs to play games: https://neftyblocks.com/collection/games4punks1/drops")

async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /linkEwallet <your_wax_wallet>")
        return

    wallet = context.args[0]
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO linked_wallets (telegram_id, wallet)
            VALUES (%s, %s)
            ON CONFLICT (telegram_id) DO UPDATE SET wallet = EXCLUDED.wallet
        """, (telegram_id, wallet))
        conn.commit()

    await update.message.reply_text(f"Wallet {wallet} linked successfully!")

async def unlink_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM linked_wallets WHERE telegram_id = %s", (telegram_id,))
        conn.commit()
    await update.message.reply_text("Wallet unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is a placeholder for actual NFT check logic
    await update.message.reply_text("YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")

async def snake_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play SnakeRun: https://hodlkong64.github.io/snakerun/")

async def emoji_punks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play Emojipunks: https://games4punks.github.io/emojisinvade/")

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=(
                f"Welcome {member.full_name}! 🎮\n"
                "To play GK Web3 games & earn FREE NFTs, you must own a GK Game Key NFT.\n"
                "Get yours here: https://neftyblocks.com/collection/games4punks1/drops"
            )
        )

def main():
    logging.basicConfig(level=logging.INFO)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("linkEwallet", link_wallet))
    application.add_handler(CommandHandler("unlinkEwallet", unlink_wallet))
    application.add_handler(CommandHandler("verifyEkey", verify_ekey))
    application.add_handler(CommandHandler("snakerun", snake_run))
    application.add_handler(CommandHandler("emojipunks", emoji_punks))
    application.add_handler(ChatMemberHandler(welcome_message, ChatMemberHandler.CHAT_MEMBER))

    application.run_polling()

if __name__ == "__main__":
    main()





