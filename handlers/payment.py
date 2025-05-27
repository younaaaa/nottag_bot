from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from services.payment import PaymentService
from utils.keyboards import payment_keyboard

def handle_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = payment_keyboard()
    query.edit_message_text(
        "درگاه پرداخت:",
        reply_markup=keyboard
    )

def setup_payment_handlers(dispatcher):
    dispatcher.add_handler(CallbackQueryHandler(handle_payment, pattern='^payment_'))