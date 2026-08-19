import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.prologue import send_prologue, prologue_next
from core import config
from core.db import init_db, create_player

# Проверка наличия токена
if not hasattr(config, 'TG_TOKEN') or not config.TG_TOKEN:
    logging.error("❌ TG_TOKEN не найден в config.py!")
    sys.exit(1)

init_db()
logging.basicConfig(level=logging.INFO)
TOKEN = config.TG_TOKEN

app = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    user_id = update.effective_user.id
    try:
        create_player(user_id)
        await send_prologue(update, context)
    except Exception as e:
        logging.error(f"Ошибка в start: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(prologue_next, pattern="^prologue_next$"))

try:
    logging.info("🚀 Бот запускается...")
    app.run_polling()
except Exception as e:
    logging.error(f"❌ Критическая ошибка: {e}")
    sys.exit(1)