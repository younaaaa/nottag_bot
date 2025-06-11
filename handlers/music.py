import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CommandHandler
)
from services.tag_editor import TagEditorService

# Define conversation states
SHOW_TAGS, AWAIT_NEW_TAG_VALUE, AWAIT_ALBUM_ART, EDIT_TAG_PROMPT = range(4) # Added AWAIT_ALBUM_ART and EDIT_TAG_PROMPT for clarity as per prompt
EDIT_CONTEXT_KEY = 'edit_music_context'

def get_edit_tags_keyboard(tags: dict, file_loaded: bool):
    buttons = []
    if not file_loaded:
        buttons.append([InlineKeyboardButton("Error: File not loaded. Try again.", callback_data="cancel_edit_tags")])
        return InlineKeyboardMarkup(buttons)

    buttons.append([InlineKeyboardButton(f"Title: {tags.get('title', 'N/A')}", callback_data="edit_tag_title")])
    buttons.append([InlineKeyboardButton(f"Artist: {tags.get('artist', 'N/A')}", callback_data="edit_tag_artist")])
    buttons.append([InlineKeyboardButton(f"Album: {tags.get('album', 'N/A')}", callback_data="edit_tag_album")])
    buttons.append([InlineKeyboardButton(f"Year: {tags.get('year', 'N/A')}", callback_data="edit_tag_year")])
    buttons.append([InlineKeyboardButton(f"Genre: {tags.get('genre', 'N/A')}", callback_data="edit_tag_genre")])
    buttons.append([InlineKeyboardButton(f"Track: {tags.get('tracknumber', 'N/A')}", callback_data="edit_tag_tracknumber")])

    buttons.append([InlineKeyboardButton("Edit Album Art (TODO)", callback_data="edit_tag_album_art")])
    buttons.append([
        InlineKeyboardButton("Save Changes", callback_data="save_tags"),
        InlineKeyboardButton("Cancel", callback_data="cancel_edit_tags")
    ])
    buttons.append([InlineKeyboardButton("Auto-fill (MusicBrainz - TODO)", callback_data="auto_fill_musicbrainz")])
    buttons.append([
        InlineKeyboardButton("Match (AcoustID - TODO)", callback_data="match_acoustid"),
        InlineKeyboardButton("Lyrics (Genius - TODO)", callback_data="search_lyrics_genius"),
    ])
    return InlineKeyboardMarkup(buttons)

async def handle_music_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    audio = message.audio
    if not audio:
        await message.reply_text("Please send an audio file.")
        return ConversationHandler.END

    file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{audio.file_unique_id}_{audio.file_name or '.tmp'}") as tmp_file:
            downloaded_file = await audio.get_file()
            await downloaded_file.download_to_drive(tmp_file.name)
            file_path = tmp_file.name

        editor = TagEditorService(file_path)
        tags = editor.get_tags()

        context.user_data[EDIT_CONTEXT_KEY] = {
            'file_path': file_path,
            'original_file_id': audio.file_id,
            'original_file_name': audio.file_name,
            'tags': tags.copy()
        }

        text = "Current tags:\n" + "\n".join([f"{k.capitalize()}: {v}" for k, v in tags.items()])
        if not tags:
            text = "No tags found or file type not fully supported. You can try editing."

        await message.reply_text(text=text, reply_markup=get_edit_tags_keyboard(tags, file_loaded=True))
        return SHOW_TAGS

    except ValueError as e:
        await message.reply_text(f"Error processing file: {e}")
        if file_path and os.path.exists(file_path): os.remove(file_path)
        return ConversationHandler.END
    except Exception as e:
        print(f"Generic error in handle_music_file: {e}")
        await message.reply_text("An unexpected error occurred.")
        if file_path and os.path.exists(file_path): os.remove(file_path)
        return ConversationHandler.END

async def cancel_edit_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()

    edit_ctx = context.user_data.pop(EDIT_CONTEXT_KEY, None)
    if edit_ctx:
        if 'file_path' in edit_ctx and os.path.exists(edit_ctx['file_path']):
            os.remove(edit_ctx['file_path'])
        if 'new_album_art_path' in edit_ctx and os.path.exists(edit_ctx['new_album_art_path']):
            os.remove(edit_ctx['new_album_art_path']) # Add this cleanup

    message_to_use = query.message if query else update.message
    if query:
        await query.edit_message_text(text="Tag editing cancelled.")
    elif message_to_use: # handle /cancel command entry
        await message_to_use.reply_text(text="Tag editing cancelled.")
    return ConversationHandler.END

async def prompt_edit_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tag_to_edit = query.data.replace('edit_tag_', '')

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'file_path' not in edit_ctx or not os.path.exists(edit_ctx['file_path']): # check file still exists
        await query.answer("Error: Session expired or file is missing. Please resend the audio file.")
        if query.message: await query.edit_message_text("Error: Session expired. Please resend the audio file.")
        return ConversationHandler.END

    edit_ctx['tag_to_edit'] = tag_to_edit
    current_value = edit_ctx['tags'].get(tag_to_edit, 'N/A')

    await query.answer()
    if query.message:
      await query.edit_message_text(text=f"Current {tag_to_edit}: {current_value}\nSend the new value for {tag_to_edit}: (or /cancel)")
    return AWAIT_NEW_TAG_VALUE

async def save_new_tag_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)

    if not edit_ctx or 'tag_to_edit' not in edit_ctx or 'file_path' not in edit_ctx or not os.path.exists(edit_ctx['file_path']):
        await update.message.reply_text("Error: Session expired or file is missing. Please start over by resending the file.")
        return ConversationHandler.END

    tag_to_edit = edit_ctx.pop('tag_to_edit')
    edit_ctx['tags'][tag_to_edit] = new_value

    text = "Updated tags (in memory):\n" + "\n".join([f"{k.capitalize()}: {v}" for k, v in edit_ctx['tags'].items()])
    await update.message.reply_text(text=text, reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True))
    return SHOW_TAGS

async def prompt_edit_album_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'file_path' not in edit_ctx:
        await query.edit_message_text("Error: File context lost. Please resend the audio file.")
        return ConversationHandler.END

    await query.edit_message_text(text="Please send a new image for the album art, or /cancel to keep the current art.")
    return AWAIT_ALBUM_ART

async def save_new_album_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)

    if not edit_ctx or 'file_path' not in edit_ctx:
        await message.reply_text("Error: File context lost. Please resend the audio file.")
        return ConversationHandler.END

    if not message.photo:
        await message.reply_text("That doesn't look like an image. Please send a photo for the album art, or use /cancel.")
        return AWAIT_ALBUM_ART

    try:
        photo_file = await message.photo[-1].get_file()

        with tempfile.NamedTemporaryFile(delete=False, suffix="_album_art.jpg") as tmp_art_file:
            await photo_file.download_to_drive(tmp_art_file.name)
            edit_ctx['new_album_art_path'] = tmp_art_file.name

        await message.reply_text(
            "New album art received. It will be applied when you 'Save Changes'.",
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True)
        )
        return SHOW_TAGS

    except Exception as e:
        print(f"Error saving new album art: {e}")
        await message.reply_text("An error occurred while processing the album art.")
        if 'new_album_art_path' in edit_ctx and os.path.exists(edit_ctx['new_album_art_path']):
            os.remove(edit_ctx['new_album_art_path'])
            del edit_ctx['new_album_art_path']
        await message.reply_text(
            "Please try sending the album art again or continue editing other tags.",
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True)
        )
        return SHOW_TAGS

async def save_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(text="Saving changes...")
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)

    if not edit_ctx or 'file_path' not in edit_ctx or not os.path.exists(edit_ctx['file_path']):
        if query.message: await query.edit_message_text("Error: File context lost or file missing. Please resend the file.")
        else: await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: File context lost. Please resend.")
        return ConversationHandler.END

    try:
        editor = TagEditorService(edit_ctx['file_path'])
        for tag_name, value in edit_ctx['tags'].items():
            if value is not None: editor.set_tag(tag_name, value)

        if 'new_album_art_path' in edit_ctx and edit_ctx['new_album_art_path']:
            try:
                with open(edit_ctx['new_album_art_path'], 'rb') as art_file_data:
                    editor.set_album_art(art_file_data.read(), mime_type='image/jpeg')
                print(f"Album art set from {edit_ctx['new_album_art_path']}")
            except Exception as e:
                print(f"Error setting album art in editor: {e}")
                await query.message.reply_text(f"Warning: Could not set new album art: {e}", parse_mode=None)

        editor.save()

        with open(edit_ctx['file_path'], 'rb') as edited_file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=edited_file,
                filename=edit_ctx.get('original_file_name', 'edited_music.dat')
            )
        if query.message: await query.edit_message_text(text="Changes saved and file sent!")

    except Exception as e:
        print(f"Error saving tags: {e}")
        if query.message: await query.edit_message_text(text=f"Error saving changes: {e}")
    finally:
        if 'new_album_art_path' in edit_ctx and edit_ctx['new_album_art_path'] and os.path.exists(edit_ctx['new_album_art_path']):
            os.remove(edit_ctx['new_album_art_path'])
        if os.path.exists(edit_ctx['file_path']): os.remove(edit_ctx['file_path'])
        context.user_data.pop(EDIT_CONTEXT_KEY, None)
    return ConversationHandler.END

async def unhandled_callback_in_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Action not implemented or unavailable.")
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if edit_ctx and 'tags' in edit_ctx and 'file_path' in edit_ctx and os.path.exists(edit_ctx['file_path']):
        await query.message.reply_text(
            text="Current tags:",
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True)
        )
        return SHOW_TAGS
    await query.message.reply_text("Session ended or context is missing. Please send an audio file again.")
    return ConversationHandler.END

async def unhandled_command_in_conv_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unrecognised commands or messages during the conversation."""
    await update.message.reply_text(
        "Unknown command or message. If you're editing tags, please send the tag value or use /cancel. "
        "Otherwise, send an audio file to start."
    )
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if edit_ctx and 'tags' in edit_ctx and 'file_path' in edit_ctx and os.path.exists(edit_ctx['file_path']):
        await update.message.reply_text(
            text="Current tags:",
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True)
        )
        return SHOW_TAGS
    return ConversationHandler.END

def setup_music_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.AUDIO, handle_music_file)],
        states={
            SHOW_TAGS: [
                CallbackQueryHandler(prompt_edit_tag, pattern="^edit_tag_(title|artist|album|year|genre|tracknumber)$"),
                CallbackQueryHandler(prompt_edit_album_art, pattern="^edit_tag_album_art$"), # Added
                CallbackQueryHandler(save_tags_handler, pattern="^save_tags$"),
                # Placeholder callbacks for other features (auto_fill, match, lyrics)
                # CallbackQueryHandler(unhandled_callback_in_conv, pattern="^auto_fill_musicbrainz$"),
                # CallbackQueryHandler(unhandled_callback_in_conv, pattern="^match_acoustid$"),
                # CallbackQueryHandler(unhandled_callback_in_conv, pattern="^search_lyrics_genius$"),
                CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
                CallbackQueryHandler(unhandled_callback_in_conv, pattern="^.*$"),
            ],
            AWAIT_NEW_TAG_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_tag_value),
                CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
                CommandHandler('cancel', cancel_edit_tags),
            ],
            AWAIT_ALBUM_ART: [ # New state
                MessageHandler(filters.PHOTO, save_new_album_art),
                CommandHandler('cancel', cancel_edit_tags),
                CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: u.message.reply_text("Please send an image or use /cancel.")),
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_edit_tags),
            CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
            # Fallback for any message or command not handled within the conversation states
            MessageHandler(filters.COMMAND | filters.TEXT, unhandled_command_in_conv_fallback)
        ],
        allow_reentry=True
    )
    application.add_handler(conv_handler)