import os
import logging
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
from flask import Flask, request

# تنظیمات اولیه
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دریافت توکن از متغیر محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN متغیر محیطی تنظیم نشده است.")

WEBHOOK_URL = f"https://api.render.com/deploy/srv-d0qfec3uibrs73ein9q0?key=gcgoD76kuL0/{8173348502:AAGgAqN4GAOSIoq5W_DCKgy9tVjb-3l7Zgk}"  # لینک خود را جایگزین کنید

# راه‌اندازی ربات تلگرام
bot = telegram.Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=4)

# تنظیمات Flask برای Webhook
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return "OK"

# دستور `/start`
def start(update, context):
    user = update.message.from_user
    logger.info(f"User {user.username} started the bot.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="سلام! خوش آمدید!")

dispatcher.add_handler(CommandHandler("start", start))

# دستور `/download` برای دانلود موسیقی از YouTube
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

# دستور `/pay` برای پرداخت با زرین‌پال
def pay(update, context):
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
