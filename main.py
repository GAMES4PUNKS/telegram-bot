import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler
import aiohttp
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")

# NFT Template IDs
GAME_KEY_TEMPLATES = [
    "898303",  # GAME-KEY-ROYALE
    "895159",  # GK3008-Game-Key
    "1099966577767"  # GAME-KEY-BATTLE-ROYALE
]

async def fetch_user_assets(wax_account):
    async with aiohttp.ClientSession() as session:
        url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?collection_name=games4punks1&owner={wax_account}&page=1&limit=100&order=desc&sort=asset_id"
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get('data', [])

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        lang = member.language_code if member.language_code else 'en'
        if lang.startswith('es'):
            msg = "🔥 Bienvenido a GKniftyHEADS! Para jugar juegos Web3 y ganar NFTs GRATIS necesitas una GAME KEY NFT: https://neftyblocks.com/collection/games4punks1/drops"
        else:
            msg = "🔥 Welcome to GKniftyHEADS! To play Web3 GK games & earn FREE NFTs you must own a GK Game Key NFT: https://neftyblocks.com/collection/games4punks1/drops"
        await context.bot.send_message(chat_id=update.chat_member.chat.id, text=msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    linked_wallet = context.chat_data.get('wax_wallet')
    if not linked_wallet:
        await update.message.reply_text("You need to /linkEwallet to check your status.")
        return

    assets = await fetch_user_assets(linked_wallet)
    owns_game_key = any(asset['template']['template_id'] in GAME_KEY_TEMPLATES for asset in assets if asset.get('template'))

    if owns_game_key:
        await update.message.reply_text("GAME SERVER IS LIVE! WHAT YOU WAITING FOR?")
    else:
        await update.message.reply_text("GK Studio is LIVE, but you need to own a Game Key NFT: https://neftyblocks.com/collection/games4punks1/drops")

async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        wax_wallet = context.args[0]
        context.chat_data['wax_wallet'] = wax_wallet
        await update.message.reply_text(f"WAX wallet {wax_wallet} linked successfully!")
    else:
        await update.message.reply_text("Usage: /linkEwallet YOUR_WAX_WALLET")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linked_wallet = context.chat_data.get('wax_wallet')
    if not linked_wallet:
        await update.message.reply_text("You need to /linkEwallet first.")
        return

    assets = await fetch_user_assets(linked_wallet)
    owns_game_key = any(asset['template']['template_id'] in GAME_KEY_TEMPLATES for asset in assets if asset.get('template'))

    if owns_game_key:
        await update.message.reply_text("YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")
    else:
        await update.message.reply_text("No valid Game Key NFT found. Please get one: https://neftyblocks.com/collection/games4punks1/drops")

async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play SnakeRun: https://hodlkong64.github.io/snakerun/")

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Play Emojipunks: https://games4punks.github.io/emojisinvade/")

async def unlink_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data.pop('wax_wallet', None)
    await update.message.reply_text("Wallet unlinked successfully.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("linkEwallet", link_wallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("snakerun", snakerun))
    app.add_handler(CommandHandler("emojipunks", emojipunks))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_wallet))

    await app.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())



