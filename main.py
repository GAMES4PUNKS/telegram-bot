import os
import logging
import asyncio
import aiohttp
import asyncpg
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Game Key NFT Templates
GAME_KEY_TEMPLATES = [
    '898303',  # GAME-KEY-ROYALE
    '895159',  # GK3008-Game-Key
    '898306'   # GAME-KEY-BATTLE-ROYALE
]

# AtomicHub API
ATOMIC_ASSETS_API = 'https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={template_id}'

# Database Connection Function
async def init_db():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise Exception("DATABASE_URL not set in environment variables.")
    conn = await asyncpg.connect(dsn=db_url)
    print("✅ Connected to PostgreSQL DB")
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS user_wallets (
            telegram_id BIGINT PRIMARY KEY,
            wallet TEXT NOT NULL
        );
    ''')
    return conn

# /start Command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('👋 Welcome to GK Games4PUNKS! Use /linkEwallet to link your WAX Wallet and start playing!')

# /status Command
async def status(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']

    row = await conn.fetchrow('SELECT wallet FROM user_wallets WHERE telegram_id = $1', telegram_id)
    if row:
        update.message.reply_text('🎮 GAME SERVER IS LIVE — WHAT YOU WAITING FOR!')
    else:
        update.message.reply_text('🕹️ GK Studio is LIVE! Purchase a Game Key NFT to play:\nhttps://neftyblocks.com/collection/games4punks1/drops')

# /linkEwallet Command
async def link_ewallet(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text('❌ Usage: /linkEwallet YOURWAXWALLET')
        return

    wallet = context.args[0].strip()
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']

    await conn.execute('''
        INSERT INTO user_wallets (telegram_id, wallet)
        VALUES ($1, $2)
        ON CONFLICT (telegram_id) DO UPDATE SET wallet = $2;
    ''', telegram_id, wallet)

    update.message.reply_text(f'🔗 Wallet {wallet} linked successfully!')

# /verifyEkey Command
async def verify_ekey(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']
    row = await conn.fetchrow('SELECT wallet FROM user_wallets WHERE telegram_id = $1', telegram_id)

    if not row:
        update.message.reply_text('❌ Link your wallet first using /linkEwallet')
        return

    wallet = row['wallet']
    async with aiohttp.ClientSession() as session:
        for template_id in GAME_KEY_TEMPLATES:
            url = ATOMIC_ASSETS_API.format(wallet=wallet, template_id=template_id)
            async with session.get(url) as resp:
                data = await resp.json()
                if data['data']:
                    update.message.reply_text('✅ YEP YOU READY FOR HODL WARS 🔥🔥🔥')
                    return
    update.message.reply_text('❌ No valid Game Key NFT found in your wallet.')

# Game Links Commands
def snakerun(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('🐍 Play SnakeRun: https://hodlkong64.github.io/snakerun/')

def emojipunks(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('🎮 Play EmojiPunks: https://games4punks.github.io/emojisinvade/')

# /unlinkEwallet Command
async def unlink_ewallet(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']

    await conn.execute('DELETE FROM user_wallets WHERE telegram_id = $1', telegram_id)
    update.message.reply_text('❌ Your wallet has been unlinked.')

# New Member Welcome
def welcome_message(update: Update, context: CallbackContext) -> None:
    for member in update.message.new_chat_members:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"👋 Welcome {member.full_name}! To play Web3 GK Games & earn FREE NFTs, you must own a GK Game Key NFT.\n👉 https://neftyblocks.com/collection/games4punks1/drops"
        )

# Main Function
async def main():
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        raise Exception("BOT_TOKEN not set in environment variables.")

    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # DB Connection
    conn = await init_db()
    dispatcher.bot_data['db_conn'] = conn

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("linkEwallet", link_ewallet))
    dispatcher.add_handler(CommandHandler("verifyEkey", verify_ekey))
    dispatcher.add_handler(CommandHandler("snakerun", snakerun))
    dispatcher.add_handler(CommandHandler("emojipunks", emojipunks))
    dispatcher.add_handler(CommandHandler("unlinkEwallet", unlink_ewallet))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    asyncio.run(main())



