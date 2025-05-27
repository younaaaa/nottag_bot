from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from utils.keyboards import music_keyboard

def handle_music(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = music_keyboard()
    query.edit_message_text(
        "مدیریت موزیک:",
        reply_markup=keyboard
    )

def setup_music_handlers(dispatcher):
    dispatcher.add_handler(CallbackQueryHandler(handle_music, pattern='^music_'))