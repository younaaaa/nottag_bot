import json
import os
from telegram.ext import ContextTypes
# Assuming database.py and models.user are set up for SQLAlchemy
from database import Session # Or your session factory
from models.user import User as UserModel # Alias to avoid conflict if User from telegram is imported

# Path to the locales directory
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locales')

loaded_locales = {}
DEFAULT_LANG = 'en'

def load_locales():
    '''Loads all .json translation files from the locales directory.'''
    global loaded_locales
    loaded_locales = {} # Clear previous loads if any
    try:
        if not os.path.exists(LOCALES_DIR):
            print(f"Locales directory not found: {LOCALES_DIR}. Creating it.")
            os.makedirs(LOCALES_DIR) # Create locales directory if it doesn't exist
            # Optionally, create dummy en.json and fa.json here for initial setup
            dummy_en = {"welcome": "Welcome!", "error_saving_lang": "Error saving language preference.", "help_message": "This is a help message."}
            dummy_fa = {"welcome": "خوش آمدید!", "error_saving_lang": "خطا در ذخیره زبان.", "help_message": "این یک پیام راهنما است."}
            with open(os.path.join(LOCALES_DIR, 'en.json'), 'w', encoding='utf-8') as f_en:
                json.dump(dummy_en, f_en, ensure_ascii=False, indent=4)
            with open(os.path.join(LOCALES_DIR, 'fa.json'), 'w', encoding='utf-8') as f_fa:
                json.dump(dummy_fa, f_fa, ensure_ascii=False, indent=4)
            print("Created dummy locale files: en.json, fa.json")

        for filename in os.listdir(LOCALES_DIR):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                filepath = os.path.join(LOCALES_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_locales[lang_code] = json.load(f)
        print(f"Loaded locales: {list(loaded_locales.keys())}")
    except Exception as e:
        print(f"Error loading locale files: {e}") # Log this properly

def get_user_language(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    '''Retrieves user language, first from context, then DB, then default.'''
    if context and context.user_data and 'selected_language' in context.user_data:
        return context.user_data['selected_language']

    # Try fetching from DB
    db_session = Session()
    try:
        user_db = db_session.query(UserModel).filter_by(user_id=user_id).first()
        if user_db and user_db.language:
            if context and hasattr(context, 'user_data'): # Ensure user_data exists
                 context.user_data['selected_language'] = user_db.language # Cache in context
            return user_db.language
    except Exception as e:
        print(f"Error fetching user language from DB for user {user_id}: {e}")
    finally:
        db_session.close()

    return DEFAULT_LANG


def get_text(key: str, context: ContextTypes.DEFAULT_TYPE = None, update = None, lang_code: str = None) -> str:
    '''
    Retrieves a translated string for a given key and language.
    Language is determined from context, or explicitly passed.
    '''
    effective_lang = DEFAULT_LANG

    if lang_code:
        effective_lang = lang_code
    elif context and hasattr(context, 'user_data') and 'selected_language' in context.user_data:
        effective_lang = context.user_data['selected_language']
    elif update and hasattr(update, 'effective_user') and update.effective_user:
        # Pass context even if it might be empty, get_user_language can handle it
        effective_lang = get_user_language(context if context else {}, update.effective_user.id)

    if not loaded_locales:
        print("Locales not loaded. Attempting to load now.")
        load_locales()
        if not loaded_locales:
             return f"ERR_NO_LOCALES_{key}"

    return loaded_locales.get(effective_lang, {}).get(key, f"_{key}_")
