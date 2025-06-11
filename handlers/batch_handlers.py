from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import os
import tempfile
from utils.i18n import get_text # Assuming this is the i18n utility
from services import TagEditorService # Ensure this import is present

# Conversation states
AWAITING_FILES, AWAITING_OPERATION_CHOICE, AWAITING_VALUE, CONFIRM_BATCH_EDIT = range(4)

BATCH_CONTEXT_KEY = 'batch_edit_context'

async def batch_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Ensure any previous batch context is cleared for this user
    if BATCH_CONTEXT_KEY in context.user_data:
        # Clean up any files from a previous aborted batch session for this user
        # This is a simplified cleanup; a more robust one might involve checking file existence
        # and handling errors if files were already moved or processed.
        old_batch_ctx = context.user_data.pop(BATCH_CONTEXT_KEY, None)
        if old_batch_ctx and old_batch_ctx.get('files'):
            print(f"Clearing {len(old_batch_ctx['files'])} files from previous batch session for user {user_id}")
            for file_info in old_batch_ctx['files']:
                if os.path.exists(file_info['path']):
                    try:
                        os.remove(file_info['path'])
                    except Exception as e:
                        print(f"Error deleting old batch temp file {file_info['path']}: {e}")

    context.user_data[BATCH_CONTEXT_KEY] = {'files': [], 'user_id': user_id}

    await update.message.reply_text(
        get_text("batch_edit_start_prompt", context, update) + "\n" +
        get_text("batch_edit_send_files_prompt", context, update) + "\n" +
        get_text("batch_edit_done_sending_command", context, update).format(command="/done_batch_files")
    )
    return AWAITING_FILES

async def batch_collect_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.audio:
        await update.message.reply_text(get_text("batch_edit_expecting_audio", context, update))
        return AWAITING_FILES

    audio = update.message.audio
    batch_ctx = context.user_data.get(BATCH_CONTEXT_KEY)
    if not batch_ctx: # Should not happen if start is the entry point
        await update.message.reply_text(get_text("error_unexpected_generic", context, update) + " (Batch context missing)")
        return ConversationHandler.END


    try:
        # Create a user-specific subdirectory within a main temp directory if it doesn't exist
        # This helps organize batch files per user.
        user_batch_dir_base = os.path.join(tempfile.gettempdir(), "bot_batch_files")
        user_specific_dir = os.path.join(user_batch_dir_base, str(update.effective_user.id))
        os.makedirs(user_specific_dir, exist_ok=True)

        # Define file path within the user-specific directory
        file_suffix = f"_{audio.file_unique_id}_{audio.file_name or '.tmp'}"
        # Use a simpler prefix, user ID is in directory path
        temp_file_path = os.path.join(user_specific_dir, f"batchfile{file_suffix}")

        downloaded_file = await audio.get_file()
        await downloaded_file.download_to_drive(temp_file_path)

        batch_ctx['files'].append({
            'path': temp_file_path,
            'original_name': audio.file_name,
            'file_id': audio.file_id
        })
        await update.message.reply_text(
            get_text("batch_edit_file_received", context, update).format(file_name=audio.file_name) + "\n" +
            get_text("batch_edit_done_sending_command_reminder", context, update).format(command="/done_batch_files")
        )
    except Exception as e:
        print(f"Error downloading batch file: {e}")
        await update.message.reply_text(get_text("batch_edit_file_download_error", context, update))

    return AWAITING_FILES

async def batch_done_sending_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    batch_ctx = context.user_data.get(BATCH_CONTEXT_KEY)
    if not batch_ctx or not batch_ctx['files']:
        await update.message.reply_text(
            get_text("batch_edit_no_files_received", context, update) + "\n" +
            get_text("batch_edit_send_files_prompt", context, update)
        )
        return AWAITING_FILES

    num_files = len(batch_ctx['files'])
    await update.message.reply_text(
        get_text("batch_edit_files_collected", context, update).format(num_files=num_files)
    )

    buttons = [
        [InlineKeyboardButton(get_text("batch_op_set_artist", context, update), callback_data="batch_op_artist")],
        [InlineKeyboardButton(get_text("batch_op_set_album", context, update), callback_data="batch_op_album")],
        [InlineKeyboardButton(get_text("batch_op_set_genre", context, update), callback_data="batch_op_genre")],
        [InlineKeyboardButton(get_text("batch_op_set_year", context, update), callback_data="batch_op_year")],
        [InlineKeyboardButton(get_text("button_cancel", context, update), callback_data="batch_op_cancel")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(get_text("batch_edit_select_operation", context, update), reply_markup=keyboard)
    return AWAITING_OPERATION_CHOICE

async def batch_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    batch_ctx = context.user_data.pop(BATCH_CONTEXT_KEY, None) # Ensure it's popped
    if batch_ctx and batch_ctx.get('files'):
        user_id = batch_ctx.get('user_id', 'unknown_user') # Get user_id from context for dir path
        print(f"Cleaning up for user {user_id} in batch_cancel. Files: {len(batch_ctx['files'])}")
        for file_info in batch_ctx['files']:
            if os.path.exists(file_info['path']):
                try:
                    os.remove(file_info['path'])
                except Exception as e:
                    print(f"Error deleting batch temp file {file_info['path']}: {e}")

        # Clean up the user-specific batch directory if it's empty
        # Note: The path construction for user_specific_dir should be consistent with batch_collect_files
        user_batch_dir_base = os.path.join(tempfile.gettempdir(), "bot_batch_files")
        user_specific_dir = os.path.join(user_batch_dir_base, str(user_id)) # Use user_id from batch_ctx
        if os.path.exists(user_specific_dir):
            try:
                if not os.listdir(user_specific_dir):
                    os.rmdir(user_specific_dir)
                    print(f"Removed empty user batch directory: {user_specific_dir}")
                else:
                    print(f"User batch directory not empty, not removing: {user_specific_dir}")
            except Exception as e:
                print(f"Error removing user batch directory {user_specific_dir}: {e}")

    if not called_from_apply:
        message_text = get_text("batch_edit_cancelled", context, update)
        if update.callback_query and update.callback_query.message:
            try:
                await update.callback_query.edit_message_text(text=message_text)
            except Exception as e:
                print(f"Error editing message in batch_cancel: {e}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)
        elif update.message:
            await update.message.reply_text(text=message_text)

    return ConversationHandler.END

async def batch_operation_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    operation = query.data.split('_')[-1]

    batch_ctx = context.user_data.get(BATCH_CONTEXT_KEY)
    if not batch_ctx: # Should exist
        await query.edit_message_text(get_text("error_unexpected_generic", context, update) + " (Batch context missing in op_selected)")
        return ConversationHandler.END
    batch_ctx['operation'] = operation

    op_text_map = {
        "artist": get_text("tag_label_artist", context, update),
        "album": get_text("tag_label_album", context, update),
        "genre": get_text("tag_label_genre", context, update),
        "year": get_text("tag_label_year", context, update),
    }
    tag_name_display = op_text_map.get(operation, operation.capitalize())

    await query.edit_message_text(
        text=get_text("batch_edit_provide_value_prompt", context, update).format(tag_name=tag_name_display)
    )
    return AWAITING_VALUE

async def batch_receive_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text
    batch_ctx = context.user_data.get(BATCH_CONTEXT_KEY)
    if not batch_ctx: # Should exist
        await update.message.reply_text(get_text("error_unexpected_generic", context, update) + " (Batch context missing in receive_value)")
        return ConversationHandler.END

    operation = batch_ctx.get('operation', 'N/A')
    num_files = len(batch_ctx.get('files', []))
    batch_ctx['value_to_set'] = value

    op_text_map = {
        "artist": get_text("tag_label_artist", context, update),
        "album": get_text("tag_label_album", context, update),
        "genre": get_text("tag_label_genre", context, update),
        "year": get_text("tag_label_year", context, update),
    }
    tag_name_display = op_text_map.get(operation, operation.capitalize())

    confirmation_text = get_text("batch_edit_confirmation_prompt", context, update).format(
        operation_name=tag_name_display,
        new_value=value,
        num_files=num_files
    )
    buttons = [
        [InlineKeyboardButton(get_text("button_confirm", context, update), callback_data="batch_confirm_apply")],
        [InlineKeyboardButton(get_text("button_cancel", context, update), callback_data="batch_op_cancel_confirm")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(text=confirmation_text, reply_markup=keyboard)
    return CONFIRM_BATCH_EDIT

async def batch_apply_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(get_text("batch_edit_applying_changes_progress", context, update))

    batch_ctx = context.user_data.get(BATCH_CONTEXT_KEY)
    if not batch_ctx or 'files' not in batch_ctx or 'operation' not in batch_ctx or 'value_to_set' not in batch_ctx:
        await query.edit_message_text(get_text("batch_edit_error_missing_context", context, update))
        return await batch_cancel(update, context, called_from_apply=True)

    files_to_process = batch_ctx['files']
    operation_tag_key = batch_ctx['operation']
    value_to_set = batch_ctx['value_to_set']

    processed_files_count = 0
    error_files_count = 0

    initial_progress_text = get_text("batch_edit_processing_files_count", context, update).format(
        num_done=0,
        num_total=len(files_to_process)
    )
    # Edit the message from the confirmation prompt
    if query.message:
        try:
            await query.edit_message_text(text=initial_progress_text)
        except Exception as e: # Message might be too old, send new one
            print(f"Error editing progress message: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=initial_progress_text)


    for i, file_info in enumerate(files_to_process):
        file_path = file_info['path']
        original_name = file_info.get('original_name', os.path.basename(file_path))
        try:
            editor = TagEditorService(file_path)
            editor.set_tag(operation_tag_key, value_to_set)
            editor.save()
            processed_files_count += 1

            try:
                with open(file_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=f,
                        filename=original_name
                    )
            except Exception as send_e:
                print(f"Error sending processed batch file {original_name}: {send_e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=get_text("batch_edit_error_sending_file", context, update).format(file_name=original_name)
                )
        except Exception as e:
            print(f"Error processing batch file {original_name}: {e}")
            error_files_count += 1
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text("batch_edit_error_processing_file", context, update).format(file_name=original_name, error_message=str(e))
            )

        if (i + 1) % 5 == 0 or (i + 1) == len(files_to_process):
            progress_update_text = get_text("batch_edit_processing_files_count", context, update).format(
                num_done=(i+1),
                num_total=len(files_to_process)
            )
            # This edit might fail if many files are processed causing delays.
            # Consider sending new messages for progress if editing becomes unreliable.
            if query.message: # Check if original message still accessible
                 try:
                     await query.edit_message_text(text=progress_update_text)
                 except Exception: # If editing fails, fall back to sending a new message for next updates
                      if (i + 1) != len(files_to_process) : # Avoid double message at the end
                           await context.bot.send_message(chat_id=update.effective_chat.id, text=progress_update_text)


    final_summary = get_text("batch_edit_completed_summary", context, update).format(
        processed_count=processed_files_count,
        error_count=error_files_count,
        total_files=len(files_to_process)
    )

    # Send final summary as a new message because the previous message might have been an error message or too old.
    await context.bot.send_message(chat_id=update.effective_chat.id, text=final_summary)

    return await batch_cancel(update, context, called_from_apply=True)


def setup_batch_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("batch_edit", batch_edit_start)],
        states={
            AWAITING_FILES: [
                MessageHandler(filters.AUDIO, batch_collect_files),
                CommandHandler("done_batch_files", batch_done_sending_files),
            ],
            AWAITING_OPERATION_CHOICE: [
                CallbackQueryHandler(batch_operation_selected, pattern="^batch_op_(artist|album|genre|year)$"),
                CallbackQueryHandler(batch_cancel, pattern="^batch_op_cancel$"), # Cancel from operation choice
            ],
            AWAITING_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, batch_receive_value),
                CallbackQueryHandler(batch_cancel, pattern="^batch_op_cancel$"), # Allow cancel during value input via a button if one were added
            ],
            CONFIRM_BATCH_EDIT: [
                CallbackQueryHandler(batch_apply_changes, pattern="^batch_confirm_apply$"), # Placeholder for apply
                CallbackQueryHandler(batch_cancel, pattern="^batch_op_cancel_confirm$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel_batch", batch_cancel),
            CallbackQueryHandler(batch_cancel, pattern="^batch_op_cancel$"), # Broad cancel
            CallbackQueryHandler(batch_cancel, pattern="^batch_op_cancel_confirm$") # Ensure this specific cancel also works
        ],
        name="batch_edit_conversation", # Optional: for debugging
        persistent=False, # Dev: False. Prod: Consider True with proper persistence backend.
    )
    application.add_handler(conv_handler)
