import logging
import asyncio
import aiohttp
import asyncpg
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = 'YOUR_BOT_TOKEN_FROM_ENV'
DATABASE_URL = 'YOUR_DATABASE_URL_FROM_ENV'

GAME_KEY_TEMPLATES = [
    '898303',  # GAME-KEY-ROYALE
    '895159',  # GK3008-Game-Key
    '898306'   # GAME-KEY-BATTLE-ROYALE
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to GK Games4PUNKS Studio!\n"
        "To play and earn FREE NFTs, you must own a GK Game Key NFT.\n"
        "Get one here: https://neftyblocks.com/collection/games4punks1/drops"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']
    row = await conn.fetchrow('SELECT wallet FROM user_wallets WHERE telegram_id = $1', telegram_id)

    if not row:
        await update.message.reply_text(
            'Yes GK Games4PUNKS Studio is LIVE!\n'
            'Purchase 1 of the available Game Key NFTs to play games:\n'
            'https://neftyblocks.com/collection/games4punks1/drops'
        )
    else:
        await update.message.reply_text('GAME SERVER IS LIVE, WHAT YOU WAITING FOR?')

async def link_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /linkEwallet YOURWAXWALLET')
        return

    wallet = context.args[0]
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']

    await conn.execute('INSERT INTO user_wallets (telegram_id, wallet) VALUES ($1, $2) ON CONFLICT (telegram_id) DO UPDATE SET wallet = $2', telegram_id, wallet)

    await update.message.reply_text(f'✅ Wallet {wallet} linked to your Telegram account.')

async def unlink_ewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']

    await conn.execute('DELETE FROM user_wallets WHERE telegram_id = $1', telegram_id)
    await update.message.reply_text('❌ Wallet unlinked.')

async def verify_ekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    conn = context.bot_data['db_conn']
    row = await conn.fetchrow('SELECT wallet FROM user_wallets WHERE telegram_id = $1', telegram_id)

    if not row:
        await update.message.reply_text('❌ Link your wallet first using /linkEwallet')
        return

    wallet = row['wallet']
    found = False

    async with aiohttp.ClientSession() as session:
        for template_id in GAME_KEY_TEMPLATES:
            url = f'https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={wallet}&template_id={template_id}'
            async with session.get(url) as resp:
                data = await resp.json()
                if data['data']:
                    found = True
                    break

    if found:
        await update.message.reply_text('✅ YEP YOU READY FOR HODL WARS 🔥🔥🔥')
    else:
        await update.message.reply_text('❌ No Game Key NFT found in your wallet.')

async def snakerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🎮 Play SnakeRun: https://hodlkong64.github.io/snakerun/')

async def emojipunks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🎮 Play EmojiPunks: https://games4punks.github.io/emojisinvade/')

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.bot_data['db_conn'] = conn

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('linkEwallet', link_ewallet))
    app.add_handler(CommandHandler('unlinkEwallet', unlink_ewallet))
    app.add_handler(CommandHandler('verifyEkey', verify_ekey))
    app.add_handler(CommandHandler('snakerun', snakerun))
    app.add_handler(CommandHandler('emojipunks', emojipunks))

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())




