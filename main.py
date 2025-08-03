import logging
from telegram import Update, ChatMember
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ChatMemberHandler
import requests

BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
GAME_KEY_TEMPLATES = [
    '898303',  # GAME-KEY-ROYALE
    '895159',  # GK3008-Game-Key
    '898306'   # GAME-KEY-BATTLE-ROYALE
]

linked_wallets = {}

def is_user_holding_game_key(wallet_address):
    url = f'https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet_address}&collection_name=games4punks1&template_whitelist={"%2C".join(GAME_KEY_TEMPLATES)}'
    response = requests.get(url)
    data = response.json()
    return len(data.get('data', [])) > 0


def welcome_new_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"👋 Welcome {member.full_name}! If you want to play Web3 GK games & earn FREE NFTs, "
                f"you need to own a GK Game Key NFT. 🎮🗝️\n\n"
                f"Purchase here 👉 https://neftyblocks.com/collection/games4punks1/drops"
            )
        )

def status_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet_address = linked_wallets.get(user_id)

    if wallet_address and is_user_holding_game_key(wallet_address):
        update.message.reply_text("🎮 GAME SERVER IS LIVE! WHAT YOU WAITING FOR!")
    else:
        update.message.reply_text(
            "🟠 Yes, GK Games4PUNKS Studio is LIVE!\n"
            "Purchase 1 of the available Game Key NFTs to play games: https://neftyblocks.com/collection/games4punks1/drops"
        )

def link_ewallet_command(update: Update, context: CallbackContext):
    if context.args:
        wallet_address = context.args[0]
        linked_wallets[update.effective_user.id] = wallet_address
        update.message.reply_text(f"🔗 Wallet {wallet_address} linked successfully!")
    else:
        update.message.reply_text("Usage: /linkEwallet YOUR_WAX_WALLET")

def unlink_ewallet_command(update: Update, context: CallbackContext):
    if update.effective_user.id in linked_wallets:
        del linked_wallets[update.effective_user.id]
        update.message.reply_text("❌ Wallet unlinked successfully.")
    else:
        update.message.reply_text("No wallet linked.")

def verify_ekey_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet_address = linked_wallets.get(user_id)

    if not wallet_address:
        update.message.reply_text("You need to link your WAX wallet first using /linkEwallet")
        return

    if is_user_holding_game_key(wallet_address):
        update.message.reply_text("✅ YEP YOU READY FOR HODL WARS ⚔️⚔️⚔️")
    else:
        update.message.reply_text("🚫 No valid Game Key NFT found. Get one here: https://neftyblocks.com/collection/games4punks1/drops")

def snakerun_command(update: Update, context: CallbackContext):
    update.message.reply_text("🐍 Play Snake Run 👉 https://hodlkong64.github.io/snakerun/")

def emojipunks_command(update: Update, context: CallbackContext):
    update.message.reply_text("🎮 Play Emojipunks 👉 https://games4punks.github.io/emojisinvade/")

def main():
    logging.basicConfig(level=logging.INFO)
    updater = Updater(BOT_TOKEN)

    dp = updater.dispatcher

    dp.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("linkEwallet", link_ewallet_command))
    dp.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet_command))
    dp.add_handler(CommandHandler("verifyEkey", verify_ekey_command))
    dp.add_handler(CommandHandler("snakerun", snakerun_command))
    dp.add_handler(CommandHandler("emojipunks", emojipunks_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

