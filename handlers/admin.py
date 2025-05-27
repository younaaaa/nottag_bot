from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from utils.keyboards import admin_keyboard
from utils.security import admin_required

@admin_required
def admin_panel(update: Update, context: CallbackContext):
    keyboard = admin_keyboard()
    update.message.reply_text(
        "پنل مدیریت:",
        reply_markup=keyboard
    )

def setup_admin_handlers(dispatcher):
    dispatcher.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_'))