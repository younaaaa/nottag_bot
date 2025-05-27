from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def get_music_keyboard():
    """منوی صفحه‌بندی شده موزیکها"""
    buttons = [
        [InlineKeyboardButton("تغییر تگ‌ها", callback_data="music_edit_tags")],
        [InlineKeyboardButton("جستجوی موزیک", callback_data="music_search")],
        [InlineKeyboardButton("◀️ بازگشت", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(buttons)