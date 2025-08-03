import os
import logging
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load BOT TOKEN from Environment Variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# List of Game Key Template IDs
TEMPLATE_IDS = ["898303", "895159", "898306"]

# Dictionary to store linked wallets (in-memory, replace with DB for production)
linked_wallets = {}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to check NFT ownership
async def check_nft_ownership(wallet: str) -> bool:
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&collection_name=games4punks1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return False
            data = await resp.json()
            for asset in data['data']:
                if asset['template']['template_id'] in TEMPLATE_IDS:
                    return True
    return False

# Welcome Message for New Group Members
def welcome(update: Update, context: CallbackContext):
    new_members = update.message.new_chat_members
    for member in new_members:
        update.message.reply_text(
            f"Welcome {member.first_name}! 🎮 To play GK Web3 Games & earn FREE NFTs, you must own a GK Game Key NFT.\n\nGet one here: https://neftyblocks.com/collection/games4punks1/drops"
        )

# /status Command
def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = linked_wallets.get(user_id)

    if wallet:
        asyncio.run(status_check(wallet, update))
    else:
        update.message.reply_text(
            "Yes GK Games4PUNKS Studio is LIVE! 🔥\nPurchase a Game Key NFT to play: https://neftyblocks.com/collection/games4punks1/drops"
        )

async def status_check(wallet, update):
    owns_nft = await check_nft_ownership(wallet)
    if owns_nft:
        update.message.reply_text("GAME SERVER IS LIVE – WHAT YOU WAITING FOR! 🚀")
    else:
        update.message.reply_text(
            "Yes GK Games4PUNKS Studio is LIVE! 🔥\nPurchase a Game Key NFT to play: https://neftyblocks.com/collection/games4punks1/drops"
        )

# /linkEwallet Command
def link_ewallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        update.message.reply_text("Usage: /linkEwallet YOURWALLET")
        return

    wallet = context.args[0]
    linked_wallets[user_id] = wallet
    update.message.reply_text(f"Wallet {wallet} linked! ✅")

# /unlinkEwallet Command
def unlink_ewallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in linked_wallets:
        del linked_wallets[user_id]
        update.message.reply_text("Wallet unlinked successfully. ❌")
    else:
        update.message.reply_text("No wallet linked to your account.")

# /verifyEkey Command
def verify_ekey(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = linked_wallets.get(user_id)

    if not wallet:
        update.message.reply_text("You need to /linkEwallet first!")
        return

    asyncio.run(verify_key(wallet, update))

async def verify_key(wallet, update):
    owns_nft = await check_nft_ownership(wallet)
    if owns_nft:
        update.message.reply_text("✅ YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")
    else:
        update.message.reply_text("❌ You don't own a valid Game Key NFT.")

# Game Links Commands
def snakerun(update: Update, context: CallbackContext):
    update.message.reply_text("🐍 Play SnakeRun: https://hodlkong64.github.io/snakerun/")

def emojipunks(update: Update, context: CallbackContext):
    update.message.reply_text("🎮 Play Emojipunks: https://games4punks.github.io/emojisinvade/")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("linkEwallet", link_ewallet))
    dp.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    dp.add_handler(CommandHandler("verifyEkey", verify_ekey))
    dp.add_handler(CommandHandler("snakerun", snakerun))
    dp.add_handler(CommandHandler("emojipunks", emojipunks))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

