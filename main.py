import os
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set. Check your Render environment variables.")

app = FastAPI()

# --- Telegram Bot Logic ---
async def bot_startup() -> None:
    print("Starting GK3008BOT...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Welcome Message Handler
    async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👾 Welcome to GK3008BOT!\n\n"
            "🎮 Available Games:\n"
            "- Emojis Invade\n"
            "- Spacerun3008\n"
            "- More coming soon!\n\n"
            "🔑 Commands:\n"
            "/linkEwallet - Link your WAX Wallet\n"
            "/verifyEkey - Verify your Game Key NFT\n"
            "/plaE - Play Emojis Invade\n"
            "\nLet’s Go, Punk!"
        )

    # Command: /linkEwallet
    async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔗 Please send your WAX wallet address to link it.")

    # Command: /verifyEkey
    async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Verifying your Game Key NFT... (WIP logic here)")

    # Command: /plaE
    async def play_emoji_invade(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎮 Play Emojis Invade here: https://games4punks.github.io/emojisinvade/")

    # Register Commands
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(CommandHandler("linkEwallet", link_ewallet))
    application.add_handler(CommandHandler("verifyEkey", verify_ekey))
    application.add_handler(CommandHandler("plaE", play_emoji_invade))

    # Start Bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.idle()

# FastAPI Startup Event
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(bot_startup())








