from telegram import Update
from telegram.ext import CallbackContext

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("در حال پردازش...")