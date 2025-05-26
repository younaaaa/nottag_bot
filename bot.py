import os
import logging
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from core.config import Config
from localization.translate import Translator
from music.youtube import download_audio
from payment.zarinpal import ZarinPal
from payment.paypal import PayPal

# تنظیمات اولیه
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
translator = Translator(lang=os.getenv("DEFAULT_LANGUAGE", "fa"))

# راه‌اندازی ربات تلگرام
bot = telegram.Bot(token=BOT_TOKEN)
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# دستور `/start`
def start(update, context):
    user = update.message.from_user
    logger.info(f"User {user.username} started the bot.")
    message = translator.translate("welcome_message")
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# دانلود موسیقی از YouTube
def download(update, context):
    url = context.args[0] if context.args else None
    if not url:
        context.bot.send_message(chat_id=update.effective_chat.id, text=translator.translate("provide_url"))
        return
    
    try:
        file_path = download_audio(url)
        context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, "rb"))
    except Exception as e:
        logger.error(f"Error downloading YouTube audio: {str(e)}")
        context.bot.send_message(chat_id=update.effective_chat.id, text=translator.translate("download_error"))

# پرداخت با زرین‌پال
def pay(update, context):
    amount = int(context.args[0]) if context.args else None
    if not amount:
        context.bot.send_message(chat_id=update.effective_chat.id, text=translator.translate("provide_amount"))
        return

    zarinpal = ZarinPal(os.getenv("ZARINPAL_MERCHANT_ID"))
    payment_data = zarinpal.create_payment(amount, "پرداخت سرویس", "https://your-website.com/callback")
    if payment_data["Status"] == 100:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"{translator.translate('payment_link')} {payment_data['payment_link']}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=translator.translate("payment_failed"))

# اضافه کردن دستورات به ربات
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("download", download))
dispatcher.add_handler(CommandHandler("pay", pay))

# اجرای ربات
if __name__ == "__main__":
    logger.info("Bot started successfully!")
    updater.start_polling()
    updater.idle()
