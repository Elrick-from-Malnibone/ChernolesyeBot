import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.prologue import send_prologue, next_prologue, skip_prologue
from core import config
from core.db import init_db, create_player

init_db()

logging.basicConfig(level=logging.INFO)

TOKEN = config.TG_TOKEN

app = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    user_id = update.effective_user.id
    create_player(user_id)
    await send_prologue(update, context)

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(next_prologue, pattern="^next_prologue$"))
app.add_handler(CallbackQueryHandler(skip_prologue, pattern="^skip_prologue$"))

app.run_polling()