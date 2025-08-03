import os
import logging
import httpx
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# --- CONFIGURATION ---
# Load environment variables from a .env file
load_dotenv()

# Your secrets and configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Details for the NFTs you want to verify
GAME_KEY_TEMPLATE_IDS = ["898303", "895159", "898306"]
MARKET_URL = "https://neftyblocks.com/collection/games4punks1/drops"
SNAKERUN_URL = "https://hodlkong64.github.io/snakerun/"
EMOJIPUNKS_URL = "https://games4punks.github.io/emojisinvade/"

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up headers for Supabase API calls
supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# --- API HELPER FUNCTIONS ---

async def check_wax_wallet_for_nft(wallet: str) -> bool:
    """Checks a WAX wallet for any of the specified Game Key NFTs."""
    # This is the public API endpoint for AtomicAssets
    url = "https://wax.api.atomicassets.io/atomicassets/v1/assets"
    
    # We check for any of the template IDs in the list
    params = {
        "owner": wallet,
        "template_whitelist": ",".join(GAME_KEY_TEMPLATE_IDS),
        "limit": 1,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # If the 'data' array is not empty, it means the user owns at least one of the NFTs
            if data.get("success") and len(data.get("data", [])) > 0:
                logger.info(f"SUCCESS: Wallet {wallet} holds a valid Game Key NFT.")
                return True
    except httpx.RequestError as e:
        logger.error(f"AtomicAssets API request failed: {e}")
        
    logger.info(f"FAILURE: Wallet {wallet} does not hold a valid Game Key NFT.")
    return False

async def get_linked_wallet(telegram_id: int) -> str | None:
    """Fetches the linked wallet address for a given Telegram ID from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets?telegram_id=eq.{telegram_id}&select=wallet"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=supabase_headers)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0].get("wallet")
    except httpx.RequestError as e:
        logger.error(f"Supabase GET request failed: {e}")
    return None

# --- TELEGRAM BOT HANDLERS ---

async def welcome_new_member(update: Update, context: CallbackContext):
    """Sends a welcome message to new members joining the group."""
    message = (
        "🔥 Welcome to GKniftyHEADS! 🔥\n\n"
        "Want to play Web3 GK games & earn FREE NFTs?\n"
        "You need a GK Game Key NFT.\n\n"
        f"Grab yours here: {MARKET_URL}"
    )
    await update.message.reply_text(message)

async def status_command(update: Update, context: CallbackContext):
    """Checks if the user has a linked wallet and if it holds a valid NFT."""
    telegram_id = update.effective_user.id
    wallet_address = await get_linked_wallet(telegram_id)

    if not wallet_address:
        await update.message.reply_text(
            f"❌ You haven't linked a wallet yet!\n"
            f"Use `/linkEwallet YOUR_WALLET_ADDRESS` in a private message with me.\n\n"
            f"Don't have a key? Get one here: {MARKET_URL}"
        )
        return

    has_nft = await check_wax_wallet_for_nft(wallet_address)
    if has_nft:
        await update.message.reply_text("✅ GAME SERVER IS LIVE! Your linked wallet holds a Game Key. Use /verifyEkey to confirm and play!")
    else:
        await update.message.reply_text(f"❌ Your linked wallet `{wallet_address}` does not hold a Game Key NFT.\n\nPurchase one here: {MARKET_URL}")


async def link_wallet_command(update: Update, context: CallbackContext):
    """Links a user's Telegram ID to their WAX wallet address in Supabase."""
    if update.message.chat.type != 'private':
        await update.message.reply_text("For your security, please use this command in a private message with me.")
        return

    if not context.args:
        await update.message.reply_text("Please provide your WAX wallet address. Usage: /linkEwallet YOUR_WALLET")
        return

    telegram_id = update.effective_user.id
    wallet = context.args[0].lower().strip()
    
    # Upsert logic: insert a new row or update it if the telegram_id already exists.
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets"
    payload = {"telegram_id": telegram_id, "wallet": wallet}
    params = {"on_conflict": "telegram_id"} # Tells Supabase what to do on conflict
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=supabase_headers, json=payload, params=params)

    if response.status_code in [200, 201, 204]:
        await update.message.reply_text(f"✅ Wallet `{wallet}` linked successfully!")
    else:
        await update.message.reply_text("❌ There was an error linking your wallet. Please try again later.")
        logger.error(f"Supabase POST error: {response.status_code} - {response.text}")


async def unlink_wallet_command(update: Update, context: CallbackContext):
    """Unlinks a user's wallet from their Telegram ID."""
    telegram_id = update.effective_user.id
    url = f"{SUPABASE_URL}/rest/v1/linked_wallets?telegram_id=eq.{telegram_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=supabase_headers)

    if response.status_code in [200, 204]:
        await update.message.reply_text("✅ Your wallet has been unlinked.")
    else:
        await update.message.reply_text("❌ Could not unlink your wallet. Perhaps you haven't linked one yet?")


async def verify_key_command(update: Update, context: CallbackContext):
    """Verifies if the user's linked wallet holds a key and grants access."""
    telegram_id = update.effective_user.id
    wallet_address = await get_linked_wallet(telegram_id)

    if not wallet_address:
        await update.message.reply_text("You need to link a wallet first with `/linkEwallet YOUR_WALLET`.")
        return

    has_nft = await check_wax_wallet_for_nft(wallet_address)
    if has_nft:
        await update.message.reply_text("✅ YEP YOU READY FOR HODL WARS! 🔥\n\nUse /snakerun or /emojipunks to play!")
    else:
        await update.message.reply_text(f"❌ Verification failed. The linked wallet `{wallet_address}` does not have a Game Key NFT.\n\nGet one here: {MARKET_URL}")

async def snakerun_command(update: Update, context: CallbackContext):
    await update.message.reply_text(f"🐍 Play Snake Run: {SNAKERUN_URL}")

async def emojipunks_command(update: Update, context: CallbackContext):
    await update.message.reply_text(f"👾 Play Emoji Punks: {EMOJIPUNKS_URL}")

# --- MAIN BOT SETUP ---
def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register all command and message handlers
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_member))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("linkEwallet", link_wallet_command))
    dp.add_handler(CommandHandler("unlinkEwallet", unlink_wallet_command))
    dp.add_handler(CommandHandler("verifyEkey", verify_key_command))
    dp.add_handler(CommandHandler("snakerun", snakerun_command))
    dp.add_handler(CommandHandler("emojipunks", emojipunks_command))
    
    # Start the Bot using polling
    logger.info("Bot is starting up...")
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
