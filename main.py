import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Command handler for /start
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_html(
        rf'Hello {user.mention_html()}! Welcome to the SPACERUN3008 game bot!',
    )

# Command handler for the game link
async def spacerun(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Click here to play SPACERUN3008: t.me/GAMES4PUNKSBOT?game=SPACERUN3008"
    )

# Command handler for /help
async def help(update: Update, context: CallbackContext):
    help_text = "Welcome to the SPACERUN3008 bot! Here's what you can do:
"                 "- /start: Start the bot and get a greeting.
"                 "- /spacerun: Get a link to play SPACERUN3008.
"                 "- /help: Get a list of available commands and instructions."
    await update.message.reply_text(help_text)

# Command handler for /userinfo
async def userinfo(update: Update, context: CallbackContext):
    user = update.effective_user
    user_info = f"User Info:
Name: {user.first_name} {user.last_name}
Username: @{user.username}
User ID: {user.id}"
    await update.message.reply_text(user_info)

# Main function to run the bot
async def main():
    bot_token = os.getenv('BOT_TOKEN')  # Get the bot token from environment variables
    application = ApplicationBuilder().token(bot_token).build()

    # Adding command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spacerun", spacerun))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("userinfo", userinfo))

    # Start the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())