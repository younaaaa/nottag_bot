import os
import logging
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
from flask import Flask, request
import threading

# تنظیمات اولیه
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دریافت توکن از متغیر محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN متغیر محیطی تنظیم نشده است.")

WEBHOOK_URL = f"https://api.render.com/deploy/{os.getenv('RENDER_SERVICE_ID')}?key={os.getenv('RENDER_API_KEY')}"

# راه‌اندازی ربات تلگرام
bot = telegram.Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=4)

# تنظیمات Flask برای Webhook
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(), bot)
    
    # پردازش به صورت چند ریسمانی
    threading.Thread(target=dispatcher.process_update, args=(update,)).start()
    
    return "OK"

# دستور `/start`
def start(update, context):
    user = update.message.from_user
    logger.info(f"User {user.username} started the bot.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="سلام! خوش آمدید!")

dispatcher.add_handler(CommandHandler("start", start))

# تابع دانلود موسیقی از یوتیوب
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

# دستور `/download` برای دانلود موسیقی
def download(update, context):
    url = context.args[0] if context.args else None
    if not url:
        context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً لینک YouTube را ارسال کنید.")
        return
    
    try:
        file_path = download_audio(url)
        context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, "rb"))
    except Exception as e:
        logger.error(f"خطا در دانلود موسیقی از یوتیوب: {str(e)}")
        context.bot.send_message(chat_id=update.effective_chat.id, text="مشکلی در دانلود موسیقی پیش آمد.")

dispatcher.add_handler(CommandHandler("download", download))

# بررسی موجود بودن کلاس زرین‌پال
try:
    from zarinpal import ZarinPal
except ImportError:
    ZarinPal = None

# دستور `/pay` برای پرداخت با زرین‌پال
def pay(update, context):
    if not ZarinPal:
        context.bot.send_message(chat_id=update.effective_chat.id, text="ماژول زرین‌پال نصب نشده است.")
        return

    amount = int(context.args[0]) if context.args else None
    if not amount:
        context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً مبلغ پرداخت را وارد کنید.")
        return

    zarinpal = ZarinPal(os.getenv("ZARINPAL_MERCHANT_ID"))
    payment_data = zarinpal.create_payment(amount, "پرداخت سرویس", "https://your-website.com/callback")
    
    if payment_data["Status"] == 100:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"لینک پرداخت: {payment_data['payment_link']}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="پرداخت ناموفق بود.")

dispatcher.add_handler(CommandHandler("pay", pay))

# تنظیم Webhook در تلگرام
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    logger.info("ربات با موفقیت راه‌اندازی شد!")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
