import os
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

# Allow nested event loops (important for Render)
nest_asyncio.apply()

# Get the BOT Token securely
BOT_TOKEN = os.getenv("BOT_TOKEN", "false")

if BOT_TOKEN == "false":
    raise ValueError("BOT_TOKEN environment variable not found!")

# Initialize FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "BOT IS LIVE AND RUNNING"}

# Command Handlers
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send me your WAX wallet address to link.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Verifying your GK3008 Game Key NFT...")

async def plae(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here is your game link: https://emojisinvade.games4punks.io")

# Async function to start Telegram Bot polling
async def start_bot():
    app_builder = ApplicationBuilder().token(BOT_TOKEN).build()

    app_builder.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app_builder.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app_builder.add_handler(CommandHandler("plaE", plae))

    print("Bot polling started...")
    await app_builder.run_polling()

# Main asyncio event loop
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        start_bot(),  # Start Telegram Bot Polling
        app.router.startup(),  # FastAPI Startup
    ))
