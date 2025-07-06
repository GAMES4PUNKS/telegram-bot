import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import nest_asyncio
import asyncio

# Fix event loop issue for Replit (Heroku should work similarly)
nest_asyncio.apply()

# Fetch Bot Token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Fetch the port from Heroku's environment variable
PORT = int(os.getenv("PORT", 8080))  # Default to 8080 if PORT isn't set

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Initialize the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# --- Global Variables ---
# Players list stored globally
players = set()

# Admin specific (replace with actual admin ID)
OWNER_CHAT_ID = 1019741898

# --- Command Handlers ---

# Define the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello, I'm your bot! Type /help for available commands.")

# Define the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Use /spacerun to play\n📊 /leaderboard for scores\n❓ /about for info"
    )

# Command handler for spacerun
async def spacerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶️ Play SPACERUN3008", url="https://t.me/GAMES4PUNKSBOT?game=SPACERUN3008")]]
    )
    await update.message.reply_text("🎮 Click below to play SPACERUN3008:", reply_markup=keyboard)

# Define a simple /about command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This bot is powered by @GAMES4PUNKSBOT – Play, Earn & Listen with SPACERUN3008!")

# --- Multi-language Support ---

async def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code
    if lang == "en":
        await update.message.reply_text("Welcome to SPACERUN3008!")
    elif lang == "es":
        await update.message.reply_text("¡Bienvenido a SPACERUN3008!")
    elif lang == "de":
        await update.message.reply_text("Willkommen bei SPACERUN3008!")
    else:
        await update.message.reply_text("Language not supported. Defaulting to English.")

# --- Admin Commands ---

# Admin Broadcast message
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_CHAT_ID:  # Replace with your Telegram user ID
        return
    if len(context.args) == 0:
        await update.message.reply_text("❌ Please provide a message to broadcast.")
        return
    msg = " ".join(context.args)
    # Assuming 'players' is a list of user IDs who are in the game
    for user_id in players:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
        except:
            continue

# Display players count
async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_CHAT_ID:  # Replace with your Telegram user ID
        await update.message.reply_text(f"👥 Total players: {len(players)}")

# --- New Member Welcome ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_member = update.message.new_chat_members[0]
    lang = new_member.language_code
    welcome_message = f"🎉 Hey {new_member.first_name}, Welcome to the **GKniftyHEADS** Family! 🎮🎉 \n\nWe're excited to have you here! Ready to play and earn WAX NFTs? 🎉\n\nHere are the awesome commands you can use to get started:\n- /spacerun – Dive into the game and start playing!\n- /leaderboard – Check out the latest scores and see how you rank.\n- /about – Find out more about the bot and how it works.\n\nLet’s have some fun! 🚀"
    
    await update.message.reply_text(welcome_message)

# --- Main function to run the bot ---
async def main():
    # Add handlers for commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("spacerun", spacerun))
    app.add_handler(CommandHandler("about", about))
    
    # Add language detection command
    app.add_handler(CommandHandler("langdetect", detect_language))

    # Admin Commands
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("players", players_command))

    # New Member Welcome
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Run the bot
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

