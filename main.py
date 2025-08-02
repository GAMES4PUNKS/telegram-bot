import os
import asyncio
from fastapi import FastAPI
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "8000"))

# Initialize FastAPI
api = FastAPI()

# Initialize Telegram Bot Application
application = Application.builder().token(TOKEN).build()

# --- BOT COMMAND HANDLERS ---

async def start(update, context):
    await update.message.reply_text("GK3008BOT is alive!")

async def link_ewallet(update, context):
    await update.message.reply_text("Link your WAX wallet here!")

async def verify_ekey(update, context):
    await update.message.reply_text("Verifying your Game Key NFT...")

async def plaE(update, context):
    await update.message.reply_text("Launching Emojis Invade game link!")

# Add command handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("linkEwallet", link_ewallet))
application.add_handler(CommandHandler("verifyEkey", verify_ekey))
application.add_handler(CommandHandler("plaE", plaE))

# --- APScheduler Example Job ---
scheduler = AsyncIOScheduler()

def scheduled_task():
    print("Scheduled task running...")

scheduler.add_job(scheduled_task, "interval", minutes=10)

# --- FastAPI Startup Event ---
@api.on_event("startup")
async def startup_event():
    print("✅ Starting Telegram Bot Polling...")
    scheduler.start()
    asyncio.create_task(application.run_polling())

# --- FastAPI Root Endpoint ---
@api.get("/")
async def root():
    return {"status": "GK3008BOT is running!"}

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:api", host="0.0.0.0", port=PORT, reload=False)


