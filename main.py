import os
import logging
import httpx
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# --- CAPTCHA & USER STATE MANAGEMENT ---
# Stores the expected captcha answer for a user
pending_captcha = {}
# Stores users who have successfully solved the captcha
verified_users = set()

# --- CAPTCHA HELPER FUNCTIONS ---
def generate_captcha(user_id):
    """Generates a math problem and stores the answer."""
    ops = ['+', '-', '*']
    operator = random.choice(ops)
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    # Ensure subtraction doesn't result in a negative number
    if operator == '-' and num1 < num2:
        num1, num2 = num2, num1

    problem = f"{num1} {operator} {num2}"
    answer = eval(problem)
    
    pending_captcha[user_id] = answer
    return f"Please solve this math problem to continue: {problem} = ?"

# --- API HELPER FUNCTIONS (SYNCHRONOUS) ---
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

# --- ORIGINAL BOT HANDLERS (CALLED BY UNIVERSAL HANDLER) ---
def welcome_new_member(update: Update, context: CallbackContext):
    message = (
        "🔥 Welcome to GKniftyHEADS! 🔥\n\n"
        "To get started, send any command like /status to verify you're a human."
    )
    update.message.reply_text(message)

def status_command(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    wallet_address = get_linked_wallet(telegram_id)
    if not wallet_address:
        update.message.reply_text(
            f"❌ You haven't linked a wallet yet!\n"
            f"Use `/linkEwallet YOUR_WALLET_ADDRESS` in a private message with me.\n\n"
            f"Don't have a key? Get one here: {MARKET_URL}"
        )
        return
    has_nft = check_wax_wallet_for_nft(wallet_address)
    if has_nft:
        update.message.reply_text("✅ GAME SERVER IS LIVE! Your linked wallet holds a Game Key. Use /verifyEkey to confirm and play!")
    else:
        update.message.reply_text(f"❌ Your linked wallet `{wallet_address}` does not hold a Game Key NFT.\n\nPurchase one here: {MARKET_URL}")

def link_wallet_command(update: Update, context: CallbackContext):
    if update.message.chat.type != 'private':
        update.message.reply_text("For your security, please use this command in a private message with me.")
        return
    if not context.args:
        update.message.reply_text("Please provide your WAX wallet address. Usage: /linkEwallet YOUR_WALLET")
        return
    telegram_id = update.effective_user.id
    wallet = context.args[0].lower().strip()
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets"
    payload = {"telegram_id": telegram_id, "wallet": wallet}
    params = {"on_conflict": "telegram_id"}
    try:
        response = httpx.post(url, headers=supabase_headers, json=payload, params=params)
        if response.status_code in [200, 201, 204]:
            update.message.reply_text(f"✅ Wallet `{wallet}` linked successfully!")
        else:
            update.message.reply_text("❌ There was an error linking your wallet. Please try again later.")
            logger.error(f"Supabase POST error: {response.status_code} - {response.text}")
    except httpx.RequestError as e:
        update.message.reply_text("❌ Could not connect to the database. Please try again later.")
        logger.error(f"Supabase POST request failed: {e}")

def unlink_wallet_command(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets?telegram_id=eq.{telegram_id}"
    try:
        response = httpx.delete(url, headers=supabase_headers)
        if response.status_code in [200, 204]:
            update.message.reply_text("✅ Your wallet has been unlinked.")
        else:
            update.message.reply_text("❌ Could not unlink your wallet. Perhaps you haven't linked one yet?")
    except httpx.RequestError as e:
        update.message.reply_text("❌ Could not connect to the database. Please try again later.")
        logger.error(f"Supabase DELETE request failed: {e}")

def verify_key_command(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    wallet_address = get_linked_wallet(telegram_id)
    if not wallet_address:
        update.message.reply_text("You need to link a wallet first with `/linkEwallet YOUR_WALLET`.")
        return
    has_nft = check_wax_wallet_for_nft(wallet_address)
    if has_nft:
        update.message.reply_text("✅ YEP YOU READY FOR HODL WARS! 🔥\n\nUse /snakerun or /emojipunks to play!")
    else:
        update.message.reply_text(f"❌ Verification failed. The linked wallet `{wallet_address}` does not have a Game Key NFT.\n\nGet one here: {MARKET_URL}")

def snakerun_command(update: Update, context: CallbackContext):
    update.message.reply_text(f"🐍 Play Snake Run: {SNAKERUN_URL}")

def emojipunks_command(update: Update, context: CallbackContext):
    update.message.reply_text(f"👾 Play Emoji Punks: {EMOJIPUNKS_URL}")

# --- UNIVERSAL HANDLER FOR CAPTCHA AND COMMAND ROUTING ---
def universal_handler(update: Update, context: CallbackContext):
    """Handles all messages to check for captcha verification before processing commands."""
    user_id = update.effective_user.id
    message_text = update.message.text

    # 1. If user is trying to solve a captcha
    if user_id in pending_captcha:
        try:
            user_answer = int(message_text)
            correct_answer = pending_captcha[user_id]
            if user_answer == correct_answer:
                verified_users.add(user_id)
                del pending_captcha[user_id]
                update.message.reply_text("✅ Correct! You are now verified and can use all commands.")
            else:
                update.message.reply_text("❌ Incorrect answer. Please try sending a command again to get a new problem.")
                del pending_captcha[user_id]
        except (ValueError, TypeError):
            update.message.reply_text("Please enter a valid number as your answer.")
        return

    # 2. If user is verified, route them to the correct command function
    if user_id in verified_users:
        command = message_text.split(' ')[0].lower()
        if command == '/status':
            return status_command(update, context)
        elif command == '/linkewallet':
            return link_wallet_command(update, context)
        elif command == '/unlinkewallet':
            return unlink_wallet_command(update, context)
        elif command == '/verifyekey':
            return verify_key_command(update, context)
        elif command == '/snakerun':
            return snakerun_command(update, context)
        elif command == '/emojipunks':
            return emojipunks_command(update, context)
        else:
            update.message.reply_text("I didn't understand that. Please use one of the available commands.")
        return

    # 3. If user is not verified and sends a command, issue a captcha
    if message_text.startswith('/'):
        captcha_question = generate_captcha(user_id)
        update.message.reply_text(f"Welcome! Before you can use commands, please verify you're a human.\n\n{captcha_question}")
    else:
        # Optional: Handle non-command messages from unverified users
        update.message.reply_text("Please start by sending a command like /status to begin verification.")

# --- MAIN BOT SETUP ---
def main():
    """Start the bot."""
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # This universal handler will manage all text and command messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, universal_handler))
    dp.add_handler(CommandHandler(["status", "linkEwallet", "unlinkEwallet", "verifyEkey", "snakerun", "emojipunks"], universal_handler))
    
    # This handler welcomes new members to the group
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_member))

    logger.info("Bot is starting up...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
