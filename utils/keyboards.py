from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 موزیک", callback_data='music_main')],
        [InlineKeyboardButton("💳 پرداخت", callback_data='payment_main')],
        [InlineKeyboardButton("⚙️ مدیریت", callback_data='admin_main')]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("آمار کاربران", callback_data='admin_stats')],
        [InlineKeyboardButton("مدیریت پرداخت‌ها", callback_data='admin_payments')]
    ])