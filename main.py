import os
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")
NFT_TEMPLATES = [
    "898303",  # GAME-KEY-ROYALE
    "895159",  # GK3008-Game-Key
    "1099966577767"  # GAME-KEY-BATTLE-ROYALE
]

app = FastAPI()

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# WELCOME MESSAGE HANDLER
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code
    message = "Welcome to GKniftyHEADS! To play Web3 GK Games & earn FREE NFTs, you must own a GK Game Key NFT: https://neftyblocks.com/collection/games4punks1/drops"
    if lang != "en":
        message += f"\n(Your detected language: {lang}. Currently, only English is supported.)"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# STATUS COMMAND
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = await get_user_wallet(user_id)
    if wallet:
        owns_key = await check_nft_ownership(wallet)
        if owns_key:
            await update.message.reply_text("GAME SERVER IS LIVE WHAT YOU WAITING FOR")
            return
    await update.message.reply_text("Yes GK Games4PUNKS Studio is LIVE, purchase 1 of 2 available Game Key NFTs to play games: https://neftyblocks.com/collection/games4punks1/drops")

# LINK EWALLET COMMAND
user_wallets = {}

async def linkEwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        wallet = context.args[0]
        user_wallets[update.effective_user.id] = wallet
        await update.message.reply_text(f"Wallet {wallet} linked successfully!")
    else:
        await update.message.reply_text("Please provide your wallet address: /linkEwallet your_wallet")

async def unlinkEwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_wallets.pop(update.effective_user.id, None)
    await update.message.reply_text("Your wallet has been unlinked.")

# VERIFY EKEY
async def verifyEkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = await get_user_wallet(user_id)
    if wallet and await check_nft_ownership(wallet):
        await update.message.reply_text("YEP YOU READY FOR HODL WARS ⚡️⚡️⚡️")
    else:
        await update.message.reply_text("No Game Key NFT found. Please purchase one to proceed.")

# GAME LINKS
async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play SnakeRun: https://hodlkong64.github.io/snakerun/")

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play Emojipunks: https://games4punks.github.io/emojisinvade/")

# UTILITIES
async def get_user_wallet(user_id):
    return user_wallets.get(user_id)

async def check_nft_ownership(wallet):
    async with httpx.AsyncClient() as client:
        url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_whitelist={','.join(NFT_TEMPLATES)}"
        response = await client.get(url)
        data = response.json()
        return len(data.get("data", [])) > 0

# REGISTER HANDLERS
telegram_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
telegram_app.add_handler(CommandHandler("status", status))
telegram_app.add_handler(CommandHandler("linkEwallet", linkEwallet))
telegram_app.add_handler(CommandHandler("unlinkEwallet", unlinkEwallet))
telegram_app.add_handler(CommandHandler("verifyEkey", verifyEkey))
telegram_app.add_handler(CommandHandler("snakerun", snakerun))
telegram_app.add_handler(CommandHandler("emojipunks", emojipunks))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_app.run_polling())

@app.get("/")
async def root():
    return {"message": "GK Bot is running"}


