import os
import logging
import httpx
import random
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GAME_KEY_TEMPLATE_IDS = ["898303", "895159", "898306"]
MARKET_URL = "https://neftyblocks.com/collection/games4punks1/drops"
SNAKERUN_URL = "https://hodlkong64.github.io/snakerun/"
EMOJIPUNKS_URL = "https://games4punks.github.io/emojisinvade/"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# --- CAPTCHA & USER STATE MANAGEMENT ---
pending_captcha = {}
verified_users = set()
pending_command = {}

# --- CUSTOM FILTER FOR CAPTCHA ANSWERS ---
class CaptchaAnswerFilter(filters.BaseFilter):
    def filter(self, message):
        # Only pay attention to messages from users who are in the pending_captcha dictionary
        return message.from_user.id in pending_captcha

# --- HELPER FUNCTIONS ---
def generate_captcha(user_id):
    """Generates a math problem and stores the answer."""
    ops = ["+", "-", "*"]
    operator = random.choice(ops)
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    if operator == "-" and num1 < num2:
        num1, num2 = num2, num1

    problem = f"{num1} {operator} {num2}"
    answer = eval(problem)

    pending_captcha[user_id] = answer
    return f"Please solve this math problem to continue: {problem} = ?"

def check_wax_wallet_for_nft(wallet: str) -> bool:
    url = "https://wax.api.atomicassets.io/atomicassets/v1/assets"
    params = {
        "owner": wallet,
        "template_whitelist": ",".join(GAME_KEY_TEMPLATE_IDS),
        "limit": 1,
    }
    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("success") and len(data.get("data", [])) > 0:
            logger.info(f"SUCCESS: Wallet {wallet} holds a valid Game Key NFT.")
            return True
    except httpx.RequestError as e:
        logger.error(f"AtomicAssets API request failed: {e}")
    logger.info(f"FAILURE: Wallet {wallet} does not hold a valid Game Key NFT.")
    return False

def get_linked_wallet(telegram_id: int) -> str | None:
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets?telegram_id=eq.{telegram_id}&select=wallet"
    try:
        response = httpx.get(url, headers=supabase_headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0].get("wallet")
    except httpx.RequestError as e:
        logger.error(f"Supabase GET request failed: {e}")
    return None

# --- BOT COMMAND HANDLERS (MUST be async for the new library version) ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🔥 Welcome to GKniftyHEADS! 🔥\n\n"
        "To get started, send `/helpme` to see how to use the bot."
    )
    await update.message.reply_text(message)

async def helpme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    help_text = (
        "Welcome! Here's how to use the bot:\n\n"
        "1️⃣ **Start by verifying you are human.** Send any command and I'll give you a simple math problem to solve.\n\n"
        "2️⃣ **Link your wallet.** Use `/linkEwallet YOUR_WALLET` in a **private message** with me to link your WAX wallet.\n\n"
        "--- **Available Commands** ---\n"
        "• `/status` - Check your wallet's verification status.\n"
        "• `/verifyEkey` - Confirm you hold the required NFT.\n"
        "• `/unlinkEwallet` - Remove your linked wallet.\n"
        "• `/snakerun` - Get the link to play Snake Run.\n"
        "• `/emojipunks` - Get the link to play Emoji Punks.\n"
        "• `/helpme` - Show this message again."
    )
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    initial_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="⏳ Checking your status..."
    )
    telegram_id = update.effective_user.id
    wallet_address = get_linked_wallet(telegram_id)
    final_text = ""
    if not wallet_address:
        final_text = (
            f"❌ You haven't linked a wallet yet!\n"
            f"Use `/linkEwallet YOUR_WALLET_ADDRESS` in a private message with me.\n\n"
            f"Don't have a key? Get one here: {MARKET_URL}"
        )
    else:
        has_nft = check_wax_wallet_for_nft(wallet_address)
        if has_nft:
            final_text = "✅ GAME SERVER IS LIVE! Your linked wallet holds a Game Key. Use `/verifyEkey` to confirm and play!"
        else:
            final_text = f"❌ Your linked wallet `{wallet_address}` does not hold a Game Key NFT.\n\nPurchase one here: {MARKET_URL}"
    await context.bot.edit_message_text(
        chat_id=initial_message.chat_id, message_id=initial_message.message_id, text=final_text
    )

async def link_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    if update.message.chat.type != "private":
        await update.message.reply_text(
            "For your security, please use this command in a private message with me."
        )
        return
    if not context.args:
        await update.message.reply_text(
            "Please provide your WAX wallet address. Usage: /linkEwallet YOUR_WALLET"
        )
        return
    initial_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🔗 Linking your wallet..."
    )
    telegram_id = update.effective_user.id
    wallet = context.args[0].lower().strip()
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets"
    payload = {"telegram_id": telegram_id, "wallet": wallet}
    params = {"on_conflict": "telegram_id"}
    final_text = ""
    try:
        response = httpx.post(url, headers=supabase_headers, json=payload, params=params)
        if response.status_code in [200, 201, 204]:
            final_text = f"✅ Wallet `{wallet}` linked successfully!"
        else:
            final_text = "❌ There was an error linking your wallet. Please try again later."
            logger.error(
                f"Supabase POST error: {response.status_code} - {response.text}"
            )
    except httpx.RequestError as e:
        final_text = "❌ Could not connect to the database. Please try again later."
        logger.error(f"Supabase POST request failed: {e}")
    await context.bot.edit_message_text(
        chat_id=initial_message.chat_id, message_id=initial_message.message_id, text=final_text
    )

async def unlink_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    initial_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🗑️ Unlinking your wallet..."
    )
    telegram_id = update.effective_user.id
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets?telegram_id=eq.{telegram_id}"
    final_text = ""
    try:
        response = httpx.delete(url, headers=supabase_headers)
        if response.status_code in [200, 204]:
            final_text = "✅ Your wallet has been unlinked."
        else:
            final_text = (
                "❌ Could not unlink your wallet. Perhaps you haven't linked one yet?"
            )
    except httpx.RequestError as e:
        final_text = "❌ Could not connect to the database. Please try again later."
        logger.error(f"Supabase DELETE request failed: {e}")
    await context.bot.edit_message_text(
        chat_id=initial_message.chat_id, message_id=initial_message.message_id, text=final_text
    )

async def verify_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    initial_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🔑 Verifying your Game Key..."
    )
    telegram_id = update.effective_user.id
    wallet_address = get_linked_wallet(telegram_id)
    final_text = ""
    if not wallet_address:
        final_text = "You need to link a wallet first with `/linkEwallet YOUR_WALLET`."
    else:
        has_nft = check_wax_wallet_for_nft(wallet_address)
        if has_nft:
            final_text = (
                "✅ YEP YOU READY FOR HODL WARS! 🔥\n\nUse `/snakerun` or `/emojipunks` to play!"
            )
        else:
            final_text = f"❌ Verification failed. The linked wallet `{wallet_address}` does not have a Game Key NFT.\n\nGet one here: {MARKET_URL}"
    await context.bot.edit_message_text(
        chat_id=initial_message.chat_id, message_id=initial_message.message_id, text=final_text
    )

async def snakerun_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    await update.message.reply_text(f"🐍 Play Snake Run: {SNAKERUN_URL}")

async def emojipunks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_message(
        chat_id=update.message.chat_id, message_id=update.message.message_id
    )
    await update.message.reply_text(f"👾 Play Emoji Punks: {EMOJIPUNKS_URL}")

# --- UNIVERSAL HANDLER FOR CAPTCHA AND COMMAND ROUTING ---
async def universal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all command messages to check for captcha verification before processing."""
    user_id = update.effective_user.id
    message_text = update.message.text

    if user_id in pending_captcha:
        if message_text.startswith("/"):
            captcha_question = generate_captcha(user_id)
            await update.message.reply_text(
                f"Please solve the math problem before using another command!\n\n{captcha_question}"
            )
            return
        try:
            user_answer = int(message_text)
            correct_answer = pending_captcha[user_id]
            if user_answer == correct_answer:
                verified_users.add(user_id)
                del pending_captcha[user_id]
                msg = await update.message.reply_text("✅ Correct! You are now verified.")
                if user_id in pending_command:
                    await context.bot.delete_message(
                        chat_id=msg.chat_id, message_id=msg.message_id
                    )
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=update.message.message_id,
                    )
                    update.message.text = pending_command[user_id]
                    await universal_handler(update, context)
                    del pending_command[user_id]
            else:
                await update.message.reply_text(
                    "❌ Incorrect answer. Please try sending a command again to get a new problem."
                )
                del pending_captcha[user_id]
        except (ValueError, TypeError):
            await update.message.reply_text("Please enter a valid number as your answer.")
        return

    if user_id in verified_users:
        command = message_text.split(" ")[0].lower()
        if command == "/status":
            await status_command(update, context)
        elif command == "/linkewallet":
            await link_wallet_command(update, context)
        elif command == "/unlinkewallet":
            await unlink_wallet_command(update, context)
        elif command == "/verifyekey":
            await verify_key_command(update, context)
        elif command == "/snakerun":
            await snakerun_command(update, context)
        elif command == "/emojipunks":
            await emojipunks_command(update, context)
        elif command == "/helpme":
            await helpme_command(update, context)
        else:
            await context.bot.delete_message(
                chat_id=update.message.chat_id, message_id=update.message.message_id
            )
            await update.message.reply_text(
                "I didn't understand that command. Use `/helpme` to see the available commands."
            )
        return

    if message_text.startswith("/"):
        pending_command[user_id] = message_text
        captcha_question = generate_captcha(user_id)
        await context.bot.delete_message(
            chat_id=update.message.chat_id, message_id=update.message.message_id
        )
        await update.message.reply_text(
            f"Welcome! Before you can use commands, please verify you're a human.\n\n{captcha_question}"
        )

# --- MAIN BOT SETUP (MODERN WEBHOOK VERSION) ---
async def main():
    """Start the bot in webhook mode."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    PORT = int(os.environ.get("PORT", "8443"))
    
    command_list = [
        "status", "linkEwallet", "unlinkEwallet", "verifyEkey",
        "snakerun", "emojipunks", "helpme",
    ]
    application.add_handler(CommandHandler(command_list, universal_handler))
    application.add_handler(
        MessageHandler(
            CaptchaAnswerFilter() & filters.TEXT & ~filters.COMMAND, universal_handler
        )
    )
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member)
    )

    logger.info("Bot is starting up in final modern webhook mode...")
    
    await application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.environ.get('RAILWAY_STATIC_URL')}"
    )

if __name__ == "__main__":
    asyncio.run(main())
