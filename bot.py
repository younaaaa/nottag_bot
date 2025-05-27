import os
from dotenv import load_dotenv
import logging
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
from flask import Flask, request
import threading

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MERCHANT_ID = os.getenv("MERCHANT_ID")

# تنظیمات لاگ‌ها
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telegram.Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=4)

app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    threading.Thread(target=dispatcher.process_update, args=(update,)).start()
    return "OK", 200

def start(update, context):
    user = update.message.from_user
    logger.info(f"User {user.username} started the bot.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="سلام! به ربات خوش آمدید!")

dispatcher.add_handler(CommandHandler("start", start))

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

def download(update, context):
    url = context.args[0] if context.args else None
    if not url:
        context.bot.send_message(chat_id=update.effective_chat.id, text="لینک YouTube را وارد کنید.")
        return
    try:
        file_path = download_audio(url)
        context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, "rb"))
    except Exception as e:
        logger.error(f"خطا در دانلود: {str(e)}")
        context.bot.send_message(chat_id=update.effective_chat.id, text="خطا در دریافت موزیک.")

dispatcher.add_handler(CommandHandler("download", download))

def pay(update, context):
    try:
        from zarinpal import ZarinPal
    except ImportError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="ماژول زرین‌پال نصب نیست.")
        return

    amount = int(context.args[0]) if context.args else None
    if not amount:
        context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً مبلغ را وارد کنید.")
        return

    zarinpal = ZarinPal(MERCHANT_ID)
    payment_data = zarinpal.create_payment(amount, "پرداخت سرویس", "https://your-website.com/callback")

    if payment_data["Status"] == 100:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"لینک پرداخت: {payment_data['payment_link']}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="پرداخت ناموفق بود.")

dispatcher.add_handler(CommandHandler("pay", pay))

bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    logger.info("ربات با موفقیت راه‌اندازی شد.")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
