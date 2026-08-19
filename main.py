import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.prologue import send_prologue, prologue_next
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
app.add_handler(CallbackQueryHandler(prologue_next, pattern="^prologue_next$"))

app.run_polling()