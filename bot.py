import os
import logging
import threading
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرها
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
RENDER_API_KEY = os.getenv("RENDER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("لطفاً BOT_TOKEN را در متغیرهای محیطی تنظیم کنید.")

WEBHOOK_URL = f"https://api.render.com/deploy/{RENDER_SERVICE_ID}?key={RENDER_API_KEY}"

# ربات تلگرام
bot = Bot(token=BOT_TOKEN)

# اطمینان از وجود دایرکتوری دانلود
os.makedirs("downloads", exist_ok=True)

# Flask app
app = Flask(__name__)

# توابع هندلر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.username} started the bot.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="سلام! خوش آمدید!")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = context.args[0] if context.args else None
    if not url:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً لینک YouTube را ارسال کنید.")
        return

    try:
        file_path = download_audio(url)
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, "rb"))
    except Exception as e:
        logger.error(f"خطا در دانلود موسیقی: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="خطایی در دانلود پیش آمد.")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from zarinpal import ZarinPal
    except ImportError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ماژول زرین‌پال نصب نیست.")
        return

    amount = int(context.args[0]) if context.args else None
    if not amount:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً مبلغ را وارد کنید.")
        return

    zarinpal = ZarinPal(os.getenv("ZARINPAL_MERCHANT_ID"))
    payment_data = zarinpal.create_payment(amount, "پرداخت سرویس", "https://your-website.com/callback")

    if payment_data.get("Status") == 100:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"لینک پرداخت: {payment_data['payment_link']}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="پرداخت ناموفق بود.")

# تابع دانلود موسیقی
def download_audio(url):
    import yt_dlp

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".mp4", ".mp3")

# ساخت اپلیکیشن تلگرام
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("download", download))
application.add_handler(CommandHandler("pay", pay))

# اتصال Flask و Telegram webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, bot)

    # پردازش Async با Thread جداگانه
    threading.Thread(target=lambda: application.update_queue.put(update)).start()
    return "OK"

# راه‌اندازی Webhook و اجرای سرور
if __name__ == "__main__":
    bot.set_webhook(url=WEBHOOK_URL)
    logger.info("ربات با موفقیت راه‌اندازی شد.")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
