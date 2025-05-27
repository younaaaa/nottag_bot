import os
import logging
import threading
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# دریافت توکن ربات از متغیر محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("متغیر محیطی BOT_TOKEN تنظیم نشده است.")
    raise ValueError("BOT_TOKEN is not set in environment variables.")

# دریافت آدرس Webhook از متغیر محیطی
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    logger.error("متغیر محیطی WEBHOOK_URL تنظیم نشده است.")
    raise ValueError("WEBHOOK_URL is not set in environment variables.")

# ایجاد نمونه ربات
bot = Bot(token=BOT_TOKEN)

# ایجاد Dispatcher برای مدیریت به‌روزرسانی‌ها
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4)

# ایجاد برنامه Flask
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """دریافت به‌روزرسانی‌ها از Telegram و پردازش آن‌ها."""
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        threading.Thread(target=dispatcher.process_update, args=(update,)).start()
    except Exception as e:
        logger.error(f"خطا در پردازش به‌روزرسانی: {e}")
    return "OK"

def start(update: Update, context: CallbackContext):
    """پاسخ به دستور /start."""
    user = update.effective_user
    logger.info(f"User {user.username} started the bot.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="سلام! خوش آمدید!")

# افزودن هندلر برای دستور /start
dispatcher.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    # تنظیم Webhook در Telegram
    try:
        bot.set_webhook(url=WEBHOOK_URL)
        logger.info("Webhook تنظیم شد.")
    except Exception as e:
        logger.error(f"خطا در تنظیم Webhook: {e}")
        raise e

    # اجرای برنامه Flask
    port = int(os.getenv("PORT", 5000))
    logger.info(f"شروع برنامه Flask در پورت {port}")
    app.run(host="0.0.0.0", port=port)
