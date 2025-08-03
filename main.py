# PostgreSQL-Powered GK Bot Core (Scalable)

import asyncio
import os
import logging
import asyncpg
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# NFT Template IDs to Check
GAME_KEYS = ["898303", "895159", "898306"]

# Logging
logging.basicConfig(level=logging.INFO)

# PostgreSQL Connection
async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

# Welcome New Members
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Welcome to GKniftyHEADS! 🎮 To play GK Games & earn FREE NFTs, own 1 of 3 GK Game Keys:\nhttps://neftyblocks.com/collection/games4punks1/drops"
        )

# /status Command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = await get_db_connection()
    wallet = await conn.fetchval('SELECT wax_wallet FROM users WHERE telegram_id = $1', user_id)
    await conn.close()

    if wallet:
        await update.message.reply_text("GAME SERVER IS LIVE — WHAT YOU WAITING FOR!")
    else:
        await update.message.reply_text("GK Studio is LIVE. Purchase a Game Key to play:\nhttps://neftyblocks.com/collection/games4punks1/drops")

# /linkEwallet Command
async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /linkEwallet <WAX_WALLET>")
        return

    wax_wallet = context.args[0]
    user_id = update.effective_user.id

    conn = await get_db_connection()
    await conn.execute(
        'INSERT INTO users (telegram_id, wax_wallet) VALUES ($1, $2) ON CONFLICT (telegram_id) DO UPDATE SET wax_wallet = $2',
        user_id, wax_wallet
    )
    await conn.close()

    await update.message.reply_text(f"Linked WAX Wallet: {wax_wallet}")

# /unlinkEwallet Command
async def unlink_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = await get_db_connection()
    await conn.execute('DELETE FROM users WHERE telegram_id = $1', user_id)
    await conn.close()

    await update.message.reply_text("Your WAX Wallet has been unlinked.")

# Simple Game Links Commands
async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play SnakeRun: https://hodlkong64.github.io/snakerun/")

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play EmojiPunks: https://games4punks.github.io/emojisinvade/")

# /verifyEkey (Placeholder for real NFT check)
async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")

# Main Application
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_wallet))
    app.add_handler(CommandHandler("snakerun", snakerun))
    app.add_handler(CommandHandler("emojipunks", emojipunks))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("start", welcome))

    # Welcome new users
    app.add_handler(CommandHandler("welcome", welcome))

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())


