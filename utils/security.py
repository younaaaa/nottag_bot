from functools import wraps
from telegram import Update
from config import Config

def admin_required(func):
    @wraps(func)
    def wrapper(update: Update, context, *args, **kwargs):
        if update.effective_user.id not in Config.ADMINS:
            update.message.reply_text("🔒 دسترسی محدود")
            return
        return func(update, context, *args, **kwargs)
    return wrapper