import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
)
import aiohttp

# Enable nested event loops for Render background worker
nest_asyncio.apply()

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

GAME_KEY_TEMPLATE_IDS = [
    898303,      # GAME-KEY-ROYALE
    895159,      # GK3008-Game-Key
    1099966577767  # GAME-KEY-BATTLE-ROYALE
]

async def check_nft_ownership(wallet_address):
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?collection_name=games4punks1&owner={wallet_address}&template_whitelist={','.join(map(str, GAME_KEY_TEMPLATE_IDS))}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return len(data.get('data', [])) > 0

# --- Commands ---

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    wallet = context.chat_data.get('wax_wallet', None)
    owns_key = False

    if wallet:
        owns_key = await check_nft_ownership(wallet)

    if owns_key:
        await context.bot.send_message(chat_id=chat_id, text="🎮 GAME SERVER IS LIVE! WHAT YOU WAITING FOR?!")
    else:
        await context.bot.send_message(chat_id=chat_id, text="GK Games4PUNKS Studio is LIVE!\nBuy your Game Key NFT here:\nhttps://neftyblocks.com/collection/games4punks1/drops")

async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /linkEwallet <your_wallet_address>")
        return

    wallet_address = context.args[0]
    context.chat_data['wax_wallet'] = wallet_address
    await update.message.reply_text(f"✅ Wallet {wallet_address} linked successfully!")

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data.pop('wax_wallet', None)
    await update.message.reply_text("❌ Wallet unlinked.")

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = context.chat_data.get('wax_wallet', None)
    if not wallet:
        await update.message.reply_text("Link your wallet first using /linkEwallet.")
        return

    owns_key = await check_nft_ownership(wallet)
    if owns_key:
        await update.message.reply_text("🎉 YEP, YOU READY FOR HODL WARS ⚡️⚡️⚡️")
    else:
        await update.message.reply_text("🚫 You don't own a Game Key NFT yet.")

async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐍 Play SNAKERUN: https://hodlkong64.github.io/snakerun/")

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👾 Play EmojiPUNKS: https://games4punks.github.io/emojisinvade/")

# --- New Member Welcome ---
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        lang_code = member.language_code or 'en'
        welcome_msg = "👋 Welcome! To play GK Web3 Games & Earn FREE NFTs, you need a Game Key NFT:\nhttps://neftyblocks.com/collection/games4punks1/drops"
        await context.bot.send_message(chat_id=update.chat_member.chat.id, text=welcome_msg)

# --- Main App ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("linkEwallet", link_ewallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    app.add_handler(CommandHandler("verifyEkey", verify_ekey))
    app.add_handler(CommandHandler("snakerun", snakerun))
    app.add_handler(CommandHandler("emojipunks", emojipunks))

    app.add_handler(ChatMemberHandler(welcome_member, ChatMemberHandler.CHAT_MEMBER))

    print("Bot is up and running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())




