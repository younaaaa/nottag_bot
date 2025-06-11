from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

# Assuming User model and SQLAlchemy session are accessible
from database import Session # Or your actual session factory
from models.user import User as UserModel # Alias to avoid conflict

from utils.i18n import get_text, DEFAULT_LANG, load_locales # Import get_text and DEFAULT_LANG

# State for language selection
SELECTING_LANG = range(1) # Unique state for this conversation

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Ensure locales are loaded (important for the first run or if not pre-loaded)
    if not hasattr(start_command, 'locales_loaded_once'):
        load_locales()
        start_command.locales_loaded_once = True # Mark as loaded to avoid redundant calls

    # Check if user exists in DB and has a language preference
    db_session = Session()
    user_db_lang = None
    try:
        user_model = db_session.query(UserModel).filter_by(user_id=user.id).first()
        if user_model and user_model.language:
            user_db_lang = user_model.language
            if context.user_data is not None: # Ensure user_data exists
                context.user_data['selected_language'] = user_db_lang
        elif user_model is None: # New user
            new_user = UserModel(user_id=user.id, username=user.username or str(user.id))
            db_session.add(new_user)
            db_session.commit()
            print(f"New user {user.id} added to DB.")

    except Exception as e:
        print(f"Error accessing DB for user {user.id} in start_command: {e}")
        db_session.rollback()
    finally:
        db_session.close()

    if user_db_lang:
        await update.message.reply_text(get_text("welcome", context, update))
        return ConversationHandler.END

    buttons = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")],
        [InlineKeyboardButton("فارسی 🇮🇷", callback_data="set_lang_fa")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "Please select your language / لطفاً زبان خود را انتخاب کنید:",
        reply_markup=keyboard
    )
    return SELECTING_LANG

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split('_')[-1]
    if context.user_data is not None:
        context.user_data['selected_language'] = lang_code

    user_id = update.effective_user.id
    username = update.effective_user.username or str(user_id) # Use ID if username is None

    db_session = Session()
    try:
        user_model = db_session.query(UserModel).filter_by(user_id=user_id).first()
        if user_model:
            user_model.language = lang_code
            if user_model.username is None and username: # Update username if it was missing
                 user_model.username = username
        else:
            # This case should ideally be handled by start_command creating the user first.
            # However, as a fallback:
            user_model = UserModel(user_id=user_id, username=username, language=lang_code)
            db_session.add(user_model)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        print(f"Error saving user language for {user_id}: {e}")
        # Try to send error in chosen lang, then default
        error_text = get_text("error_saving_lang", context, update, lang_code=lang_code)
        if "_error_saving_lang_" in error_text: # Key not found in chosen lang
            error_text = get_text("error_saving_lang", context, update, lang_code=DEFAULT_LANG)
        await query.edit_message_text(text=error_text)
        return ConversationHandler.END
    finally:
        db_session.close()

    await query.edit_message_text(text=get_text("welcome", context, update))
    return ConversationHandler.END

def setup_general_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            SELECTING_LANG: [
                CallbackQueryHandler(set_language_callback, pattern="^set_lang_"),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    application.add_handler(conv_handler)

    # Example for a /help command using i18n
    # async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     # Ensure language is loaded for the user for help_message
    #     if context.user_data and 'selected_language' not in context.user_data and update.effective_user:
    #         get_user_language(context, update.effective_user.id) # This will load and cache it
    #     await update.message.reply_text(get_text("help_message", context, update))
    # application.add_handler(CommandHandler("help", help_command))
