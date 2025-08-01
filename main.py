
import logging
import os
import aiohttp
import nest_asyncio
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from db import init_db, link_wallet, get_wallet, unlink_wallet, set_verified

nest_asyncio.apply()
BOT_TOKEN = os.getenv("BOT_TOKEN")

EMOJI_GAME_URL = "https://games4punks.github.io/emojisinvade/"
SPACERUN_GAME_URL = "https://games4punks.github.io/spacerun3008/"
TEMPLATE_LINK = "https://wax.atomichub.io/explorer/template/wax-mainnet/games4punks1/GK3008-Game-Key_895159"
ATOMIC_API = "https://wax.api.atomicassets.io/atomicassets/v1/assets"
GAME_KEY_TEMPLATE_ID = "895159"
OWNER_CHAT_ID = 1019741898

logging.basicConfig(level=logging.INFO)

async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link your WAX wallet using /linkEwallet.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Play SPACERUN3008", url=SPACERUN_GAME_URL)]])
                await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy it here:\n{TEMPLATE_LINK}")

async def play_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You must link your WAX wallet using /linkEwallet.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                await update.message.reply_text(f"🎮 [▶ Play Emojis Invade]({EMOJI_GAME_URL})", parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy one:\n{TEMPLATE_LINK}")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ No wallet linked. Use /linkEwallet first.")
        return
    url = f"{ATOMIC_API}?owner={wallet}&template_id={GAME_KEY_TEMPLATE_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            if data.get("data"):
                set_verified(user_id, wallet)
                await update.message.reply_text("✅ Your Game Key NFT is verified. You now have access to all games.")
            else:
                await update.message.reply_text(f"❌ You don’t own the Game Key NFT.\nBuy one here:\n{TEMPLATE_LINK}")

async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧾 Send your WAX wallet (e.g., abcd.wam):")
    return 1

async def save_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text.strip()
    if wallet.endswith(".wam") and len(wallet) <= 15 and wallet.replace('.', '').isalnum():
        link_wallet(update.effective_user.id, wallet)
        await update.message.reply_text(f"✅ WAX wallet `{wallet}` linked!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Invalid wallet format. Try again.")
    return ConversationHandler.END

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_wallet(user_id):
        unlink_wallet(user_id)
        await update.message.reply_text("❎ Your WAX wallet has been unlinked.")
    else:
        await update.message.reply_text("⚠️ No wallet is currently linked.")

async def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("plaE", play_emoji))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("linkEwallet", link_ewallet)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_wallet)]},
        fallbacks=[]
    ))
    print("✅ Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
