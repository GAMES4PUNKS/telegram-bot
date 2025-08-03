import os
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

# Force asyncio to allow nested loops (Render)
nest_asyncio.apply()

# Get BOT TOKEN from Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "false")

if BOT_TOKEN == "false":
    raise ValueError("BOT_TOKEN environment variable not set in Render Dashboard.")

# FastAPI App (dummy endpoint for Render healthcheck)
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot is running"}

# Command Handlers
async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send me your WAX wallet address to link.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Verifying your GK3008 Game Key NFT...")

async def plae(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here is your game link: https://emojisinvade.games4punks.io")

# Polling Loop Function
async def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("linkEwallet", link_ewallet))
    application.add_handler(CommandHandler("verifyEkey", verify_ekey))
    application.add_handler(CommandHandler("plaE", plae))

    # Start polling forever
    await application.run_polling()

# Startup Event
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())









