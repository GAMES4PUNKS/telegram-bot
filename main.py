import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler
from langdetect import detect

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Make sure BOT_TOKEN is set in Render environment

GAME_KEYS = [
    "898303",  # GAME-KEY-ROYALE
    "895159"   # GK3008-Game-Key
]

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member.new_chat_member.status == "member":
        user = update.chat_member.from_user
        try:
            language = detect(user.first_name)  # Detect language from user first name (very basic)
        except:
            language = "en"
        msg = (
            "🔥 Welcome to GKniftyHEADS 🔥\n\n"
            "Wanna play Web3 GK Games & earn FREE NFTs?\n"
            "You need a GK Game Key NFT to unlock it all:\n"
            "👉 https://neftyblocks.com/collection/games4punks1/drops"
        )
        await context.bot.send_message(chat_id=update.chat_member.chat.id, text=msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Placeholder check for NFT ownership (replace with actual check later)
    has_game_key = False  # Assume false for now (needs AtomicHub API integration)

    if has_game_key:
        await update.message.reply_text("🎮 GAME SERVER IS LIVE! WHAT YOU WAITING FOR?")
    else:
        await update.message.reply_text(
            "❌ You need a GK Game Key NFT to play:\n"
            "👉 https://neftyblocks.com/collection/games4punks1/drops"
        )

async def verifyEkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder logic
    await update.message.reply_text("✅ YEP YOU READY FOR HODL WARS ⚡⚡⚡")

async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐍 Play SnakeRun: https://hodlkong64.github.io/snakerun/")

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 Play EmojiPunks: https://games4punks.github.io/emojisinvade/")

async def linkEwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 Send your WAX Wallet Address to link it.")

async def unlinkEwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Your WAX Wallet has been unlinked.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatMemberHandler(welcome_message, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("verifyEkey", verifyEkey))
    app.add_handler(CommandHandler("snakerun", snakerun))
    app.add_handler(CommandHandler("emojipunks", emojipunks))
    app.add_handler(CommandHandler("linkEwallet", linkEwallet))
    app.add_handler(CommandHandler("unlinkEwallet", unlinkEwallet))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

