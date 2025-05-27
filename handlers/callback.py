from telegram import Update
from telegram.ext import CallbackContext

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE)
    query = update.callback_query
    query.answer("در حال پردازش...")