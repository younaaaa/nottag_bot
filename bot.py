import os
from flask import Flask, request
from telegram import Bot, Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import logging

# تنظیمات اولیه
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-url.onrender.com")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# لاگ‌ها
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.info("ربات با موفقیت راه‌اندازی شد.")

# دکمه‌های Reply (منوی اصلی)
main_menu_fa = ReplyKeyboardMarkup(
    keyboard=[
        ["🔍 جستجوی آهنگ", "🛒 خرید اشتراک"],
        ["📊 وضعیت اشتراک", "❓ راهنما"]
    ],
    resize_keyboard=True
)

main_menu_en = ReplyKeyboardMarkup(
    keyboard=[
        ["🔍 Search Song", "🛒 Buy Subscription"],
        ["📊 My Status", "❓ Help"]
    ],
    resize_keyboard=True
)

# دکمه‌های Inline
def get_inline_buttons_fa(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ دانلود آهنگ", url=link)],
        [InlineKeyboardButton("🎵 اشتراک ویژه", callback_data="buy_premium")]
    ])

def get_inline_buttons_en(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download Song", url=link)],
        [InlineKeyboardButton("🎵 Buy Premium", callback_data="buy_premium")]
    ])

# تابع تشخیص زبان کاربر (به صورت ساده، قابل توسعه با ذخیره‌سازی زبان کاربر)
def get_user_language(user_id):
    # می‌توان از دیتابیس استفاده کرد، فعلاً فرض بر فارسی است
    return "fa"

# دستورات
def start(update: Update, context: CallbackContext):
    lang = get_user_language(update.effective_user.id)
    if lang == "fa":
        update.message.reply_text("سلام! به ربات موزیک خوش اومدی 🎶", reply_markup=main_menu_fa)
    else:
        update.message.reply_text("Hi! Welcome to the Music Bot 🎶", reply_markup=main_menu_en)

def help_command(update: Update, context: CallbackContext):
    lang = get_user_language(update.effective_user.id)
    if lang == "fa":
        update.message.reply_text("برای استفاده، فقط اسم آهنگ رو بفرست یا از منو استفاده کن.")
    else:
        update.message.reply_text("Just send the song name or use the menu.")

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    lang = get_user_language(update.effective_user.id)
    dummy_link = "https://example.com/song.mp3"
    if lang == "fa":
        update.message.reply_text(f"آهنگ '{text}' پیدا شد 🎧", reply_markup=get_inline_buttons_fa(dummy_link))
    else:
        update.message.reply_text(f"The song '{text}' was found 🎧", reply_markup=get_inline_buttons_en(dummy_link))

def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data == "buy_premium":
        lang = get_user_language(query.from_user.id)
        query.answer()
        if lang == "fa":
            query.edit_message_text("برای خرید اشتراک، به لینک زیر برو:\nhttps://yourdomain.com/buy")
        else:
            query.edit_message_text("To buy a premium subscription, visit:\nhttps://yourdomain.com/buy")

# ثبت هندلرها
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

# وبهوک برای Flask
@app.route('/', methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# راه‌اندازی وبهوک هنگام اجرای مستقیم
if __name__ == '__main__':
    bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=10000)
