from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from config import Config
import logging

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دستور /start"""
    await update.message.reply_text("به ربات خوش آمدید!")

def main():
    # ساخت نمونه Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", start))
    
    # شروع ربات
    application.run_polling()

if __name__ == '__main__':
    main()