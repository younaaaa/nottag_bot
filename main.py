from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    CallbackContext  # برای سازگاری با کدهای قدیمی
)
from handlers import setup_handlers
from config import Config
import logging

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    """عملیات پس از مقداردهی اولیه"""
    await application.bot.set_my_commands([
        ("start", "شروع ربات"),
        ("help", "راهنما")
    ])

def main():
    # ساخت نمونه Application
    application = Application.builder() \
        .token(Config.BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # تنظیم هندلرها
    setup_handlers(application)
    
    # شروع ربات
    application.run_polling()

if __name__ == '__main__':
    main()