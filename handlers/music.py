from telegram import Update
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

async def handle_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دستورات موزیک"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="لطفاً یک آهنگ ارسال کنید:",
        reply_markup=await get_music_keyboard()
    )

async def handle_music_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل موزیک"""
    music_file = await update.message.audio.get_file()
    await update.message.reply_text("فایل موزیک دریافت شد!")

def setup_music_handlers(application):
    """ثبت هندلرهای موزیک"""
    application.add_handler(CallbackQueryHandler(handle_music, pattern="^music_"))
    application.add_handler(MessageHandler(filters.AUDIO, handle_music_file))