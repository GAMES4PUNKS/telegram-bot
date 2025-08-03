import os
import aiohttp
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
user_wallets = {}  # user_id: wallet_address
verified_holders = set()

GAME_KEY_TEMPLATES = [
    "898303",  # GAME-KEY-ROYALE
    "895159"   # GK3008-Game-Key
]

async def check_nft_ownership(wallet: str) -> bool:
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_whitelist={','.join(GAME_KEY_TEMPLATES)}&collection_name=games4punks1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data['data'] != []

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_wallets:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You need to link your WAX Wallet first! Use /linkEwallet")
        return

    wallet = user_wallets[user_id]
    owns_nft = await check_nft_ownership(wallet)

    if owns_nft:
        verified_holders.add(user_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ GAME SERVER IS LIVE — WHAT YOU WAITING FOR?")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="GK Studio is LIVE but you need a Game Key NFT to play! Get yours here: https://neftyblocks.com/collection/games4punks1/drops")

async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /linkEwallet YOUR_WAX_WALLET")
        return

    user_id = update.effective_user.id
    wallet = context.args[0]
    user_wallets[user_id] = wallet
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Wallet {wallet} linked successfully!")

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_wallets.pop(user_id, None)
    verified_holders.discard(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Your wallet has been unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_holders:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Link your wallet with /linkEwallet and verify ownership first!")

async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_holders:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Play SnakeRun: https://hodlkong64.github.io/snakerun/")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You need to verify NFT ownership first with /linkEwallet and /verifyEkey")

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_holders:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Play Emojis Invade: https://games4punks.github.io/emojisinvade/")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You need to verify NFT ownership first with /linkEwallet and /verifyEkey")

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_members = update.message.new_chat_members
    for member in new_members:
        lang = update.effective_user.language_code
        if lang == 'es':
            msg = "Bienvenido a GKniftyHEADS! Para jugar juegos Web3 GK y ganar NFTs GRATIS necesitas una Game Key NFT: https://neftyblocks.com/collection/games4punks1/drops"
        else:
            msg = "Welcome to GKniftyHEADS! To play GK Web3 games & earn FREE NFTs you need a Game Key NFT: https://neftyblocks.com/collection/games4punks1/drops"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

@app.on_event("startup")
async def startup_event():
    app.telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.telegram_app.add_handler(CommandHandler("status", status))
    app.telegram_app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.telegram_app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.telegram_app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.telegram_app.add_handler(CommandHandler("snakerun", snakerun))
    app.telegram_app.add_handler(CommandHandler("emojipunks", emojipunks))
    app.telegram_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))
    asyncio.create_task(app.telegram_app.run_polling())

@app.get("/")
async def root():
    return {"status": "Bot is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
