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
from services import MusicBrainzService, AcoustIDService, GeniusService
from utils.i18n import get_text # Added i18n import

# Define conversation states
SHOW_TAGS, AWAIT_NEW_TAG_VALUE, AWAIT_ALBUM_ART, EDIT_TAG_PROMPT, AWAIT_MB_SELECTION, AWAIT_ACOUSTID_SELECTION = range(6)
EDIT_CONTEXT_KEY = 'edit_music_context'

# Modified signature to include context and update for i18n
def get_edit_tags_keyboard(tags: dict, file_loaded: bool, context: ContextTypes.DEFAULT_TYPE, update: Update):
    buttons = []
    if not file_loaded:
        buttons.append([InlineKeyboardButton(get_text("error_file_not_loaded_try_again", context, update), callback_data="cancel_edit_tags")])
        return InlineKeyboardMarkup(buttons)

    na_text = get_text("tag_value_not_available", context, update)
    buttons.append([InlineKeyboardButton(f"{get_text('tag_label_title', context, update)}: {tags.get('title', na_text)}", callback_data="edit_tag_title")])
    buttons.append([InlineKeyboardButton(f"{get_text('tag_label_artist', context, update)}: {tags.get('artist', na_text)}", callback_data="edit_tag_artist")])
    buttons.append([InlineKeyboardButton(f"{get_text('tag_label_album', context, update)}: {tags.get('album', na_text)}", callback_data="edit_tag_album")])
    buttons.append([InlineKeyboardButton(f"{get_text('tag_label_year', context, update)}: {tags.get('year', na_text)}", callback_data="edit_tag_year")])
    buttons.append([InlineKeyboardButton(f"{get_text('tag_label_genre', context, update)}: {tags.get('genre', na_text)}", callback_data="edit_tag_genre")])
    buttons.append([InlineKeyboardButton(f"{get_text('tag_label_tracknumber', context, update)}: {tags.get('tracknumber', na_text)}", callback_data="edit_tag_tracknumber")])

    buttons.append([InlineKeyboardButton(get_text("button_edit_album_art", context, update), callback_data="edit_tag_album_art")])
    buttons.append([
        InlineKeyboardButton(get_text("button_save_changes", context, update), callback_data="save_tags"),
        InlineKeyboardButton(get_text("button_cancel", context, update), callback_data="cancel_edit_tags")
    ])
    buttons.append([InlineKeyboardButton(get_text("button_autofill_musicbrainz", context, update), callback_data="auto_fill_musicbrainz")])
    buttons.append([
        InlineKeyboardButton(get_text("button_match_acoustid", context, update), callback_data="match_acoustid"),
        InlineKeyboardButton(get_text("button_lyrics_genius", context, update), callback_data="search_lyrics_genius"),
    ])
    return InlineKeyboardMarkup(buttons)

async def handle_music_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    audio = message.audio
    if not audio:
        await message.reply_text(get_text("prompt_send_audio_file", context, update))
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

        text_header = get_text("header_current_tags", context, update)
        tag_lines = "\n".join([f"{key.capitalize()}: {value}" for key, value in tags.items()]) # Keep system values for keys for now

        text_content = tag_lines if tags else get_text("info_no_tags_found_try_edit", context, update)
        full_text = f"{text_header}\n{text_content}"

        await message.reply_text(
            text=full_text,
            reply_markup=get_edit_tags_keyboard(tags, file_loaded=True, context=context, update=update) # Pass context & update
        )
        return SHOW_TAGS

    except ValueError as e:
        await message.reply_text(get_text("error_processing_file", context, update).format(error_message=str(e)))
        if file_path and os.path.exists(file_path): os.remove(file_path)
        return ConversationHandler.END
    except Exception as e:
        print(f"Generic error in handle_music_file: {e}")
        await message.reply_text(get_text("error_processing_music_file_unexpected", context, update))
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
            os.remove(edit_ctx['new_album_art_path'])

    message_to_use = query.message if query else update.message
    text_cancelled = get_text("info_tag_editing_cancelled", context, update)
    if query:
        await query.edit_message_text(text=text_cancelled)
    elif message_to_use:
        await message_to_use.reply_text(text=text_cancelled)
    return ConversationHandler.END

async def prompt_edit_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tag_to_edit_key = query.data.replace('edit_tag_', '') # e.g., 'title'

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'file_path' not in edit_ctx or not os.path.exists(edit_ctx['file_path']):
        await query.answer(get_text("error_session_expired_resend_audio", context, update)) # Answer callback
        if query.message: await query.edit_message_text(get_text("error_session_expired_resend_audio", context, update))
        return ConversationHandler.END

    edit_ctx['tag_to_edit'] = tag_to_edit_key
    current_value = edit_ctx['tags'].get(tag_to_edit_key, get_text("tag_value_not_available", context, update))

    # For user display, get translated tag name if we have a key for it
    tag_name_display = get_text(f"tag_label_{tag_to_edit_key.lower()}", context, update)
    if f"_{tag_to_edit_key.lower()}_" in tag_name_display: # Fallback if no specific label key
        tag_name_display = tag_to_edit_key.capitalize()

    prompt_text = get_text("prompt_edit_tag_current_value", context, update).format(
        tag_name=tag_name_display,
        tag_value=current_value
    )
    await query.answer()
    if query.message:
      await query.edit_message_text(text=prompt_text)
    return AWAIT_NEW_TAG_VALUE

async def save_new_tag_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)

    if not edit_ctx or 'tag_to_edit' not in edit_ctx or 'file_path' not in edit_ctx or not os.path.exists(edit_ctx['file_path']):
        await update.message.reply_text(get_text("error_session_expired_start_over", context, update))
        return ConversationHandler.END

    tag_to_edit = edit_ctx.pop('tag_to_edit')
    edit_ctx['tags'][tag_to_edit] = new_value

    text_header = get_text("header_updated_tags_in_memory", context, update)
    tag_lines = "\n".join([f"{key.capitalize()}: {value}" for key, value in edit_ctx['tags'].items()])
    full_text = f"{text_header}\n{tag_lines}"

    await update.message.reply_text(
        text=full_text,
        reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
    )
    return SHOW_TAGS

async def prompt_edit_album_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'file_path' not in edit_ctx:
        await query.edit_message_text(get_text("error_file_context_lost_resend_audio", context, update))
        return ConversationHandler.END

    await query.edit_message_text(text=get_text("prompt_send_album_art_or_cancel", context, update))
    return AWAIT_ALBUM_ART

async def save_new_album_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)

    if not edit_ctx or 'file_path' not in edit_ctx:
        await message.reply_text(get_text("error_file_context_lost_resend_audio", context, update))
        return ConversationHandler.END

    if not message.photo:
        await message.reply_text(get_text("error_not_an_image_send_photo_or_cancel", context, update))
        return AWAIT_ALBUM_ART

    try:
        photo_file = await message.photo[-1].get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix="_album_art.jpg") as tmp_art_file:
            await photo_file.download_to_drive(tmp_art_file.name)
            edit_ctx['new_album_art_path'] = tmp_art_file.name

        await message.reply_text(
            get_text("info_new_album_art_received_apply_on_save", context, update),
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS
    except Exception as e:
        print(f"Error saving new album art: {e}")
        await message.reply_text(get_text("error_processing_album_art", context, update))
        if 'new_album_art_path' in edit_ctx and os.path.exists(edit_ctx['new_album_art_path']):
            os.remove(edit_ctx['new_album_art_path'])
            del edit_ctx['new_album_art_path']
        await message.reply_text(
            get_text("prompt_try_album_art_again_or_continue", context, update),
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

async def save_tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(get_text("info_saving_changes", context, update))
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)

    if not edit_ctx or 'file_path' not in edit_ctx or not os.path.exists(edit_ctx['file_path']):
        text_error = get_text("error_file_context_lost_or_missing_resend", context, update)
        if query.message: await query.edit_message_text(text_error)
        else: await context.bot.send_message(chat_id=update.effective_chat.id, text=text_error)
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
                await query.message.reply_text(get_text("warning_could_not_set_album_art", context, update).format(error_message=str(e)))
        editor.save()

        with open(edit_ctx['file_path'], 'rb') as edited_file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=edited_file,
                filename=edit_ctx.get('original_file_name', 'edited_music.dat')
            )
        if query.message: await query.edit_message_text(text=get_text("info_changes_saved_file_sent", context, update))
    except Exception as e:
        print(f"Error saving tags: {e}")
        if query.message: await query.edit_message_text(text=get_text("error_saving_changes", context, update).format(error_message=str(e)))
    finally:
        if 'new_album_art_path' in edit_ctx and edit_ctx['new_album_art_path'] and os.path.exists(edit_ctx['new_album_art_path']):
            os.remove(edit_ctx['new_album_art_path'])
        if 'file_path' in edit_ctx and os.path.exists(edit_ctx['file_path']): os.remove(edit_ctx['file_path']) # Check key exists
        context.user_data.pop(EDIT_CONTEXT_KEY, None)
    return ConversationHandler.END

async def auto_fill_musicbrainz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(get_text("info_searching_musicbrainz", context, update))

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'tags' not in edit_ctx:
        await query.edit_message_text(get_text("error_original_tags_not_found", context, update))
        return SHOW_TAGS

    current_tags = edit_ctx.get('tags', {})
    title = current_tags.get('title')
    artist = current_tags.get('artist')

    if not title and not artist:
        await query.edit_message_text(
            get_text("error_need_title_or_artist_for_mb_search", context, update),
            reply_markup=get_edit_tags_keyboard(current_tags, file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

    try:
        mb_service = MusicBrainzService()
        results = mb_service.search_track(artist_name=artist, track_title=title, limit=5)
    except ValueError as e:
         await query.edit_message_text(get_text("error_musicbrainz_service", context, update).format(error_message=str(e)))
         return SHOW_TAGS
    except Exception as e:
         await query.edit_message_text(get_text("error_searching_musicbrainz", context, update).format(error_message=str(e)))
         print(f"MusicBrainz search error: {e}")
         return SHOW_TAGS

    if not results:
        await query.edit_message_text(
            get_text("info_no_results_musicbrainz", context, update),
            reply_markup=get_edit_tags_keyboard(current_tags, file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

    buttons = []
    if results:
        for i, track in enumerate(results):
            button_text = f"{track.get('title', get_text('tag_value_not_available', context, update))} by {track.get('artist', get_text('tag_value_not_available', context, update))}"
            if track.get('album'):
                button_text += f" ({track.get('album')})"
            if track.get('year'):
                button_text += f" - {track.get('year')}"
            context.user_data[f"mb_result_{i}"] = track
            buttons.append([InlineKeyboardButton(button_text[:64], callback_data=f"mb_select_{i}_{track.get('id', '')}")])

    if not buttons:
         await query.edit_message_text(
            get_text("error_mb_results_display_error", context, update),
            reply_markup=get_edit_tags_keyboard(current_tags, file_loaded=True, context=context, update=update)
        )
         return SHOW_TAGS

    buttons.append([InlineKeyboardButton(get_text("button_cancel_autofill", context, update), callback_data="mb_cancel_autofill")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(get_text("prompt_select_match_musicbrainz", context, update), reply_markup=reply_markup)
    return AWAIT_MB_SELECTION

async def handle_mb_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selection_parts = query.data.split('_')
    result_key_index = selection_parts[2]

    selected_track_info = context.user_data.pop(f"mb_result_{result_key_index}", None)
    for i in range(5):
         context.user_data.pop(f"mb_result_{i}", None)

    if not selected_track_info:
        await query.edit_message_text(get_text("error_could_not_retrieve_selection", context, update))
        edit_ctx_fallback = context.user_data.get(EDIT_CONTEXT_KEY, {'tags': {}})
        reply_target = query.message if query.message else update.effective_message
        await reply_target.reply_text( # Send as new message if edit_message_text source is gone
            get_text("info_returning_to_tag_editor", context, update),
            reply_markup=get_edit_tags_keyboard(edit_ctx_fallback.get('tags',{}), file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx:
        await query.edit_message_text(get_text("error_critical_editing_context_lost", context, update))
        return ConversationHandler.END

    if selected_track_info.get('title'): edit_ctx['tags']['title'] = selected_track_info['title']
    if selected_track_info.get('artist'): edit_ctx['tags']['artist'] = selected_track_info['artist']
    if selected_track_info.get('album'): edit_ctx['tags']['album'] = selected_track_info['album']
    if selected_track_info.get('year'): edit_ctx['tags']['year'] = selected_track_info['year']

    await query.edit_message_text(
        get_text("info_tags_updated_from_musicbrainz", context, update),
        reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
    )
    return SHOW_TAGS

async def handle_mb_cancel_autofill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    for i in range(5):
         context.user_data.pop(f"mb_result_{i}", None)

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY, {'tags': {}})
    await query.edit_message_text(
        get_text("info_autofill_cancelled_returning_to_editor", context, update),
        reply_markup=get_edit_tags_keyboard(edit_ctx.get('tags',{}), file_loaded=True, context=context, update=update)
    )
    return SHOW_TAGS

async def match_acoustid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(get_text("info_fingerprinting_acoustid", context, update))

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'file_path' not in edit_ctx:
        await query.edit_message_text(get_text("error_file_path_not_found_resend_audio", context, update))
        return SHOW_TAGS

    file_path = edit_ctx['file_path']
    current_tags = edit_ctx.get('tags', {})

    try:
        acoustid_service = AcoustIDService()
        acoustid_results = acoustid_service.lookup_fingerprint(file_path)
    except ValueError as e:
         await query.edit_message_text(get_text("error_acoustid_service", context, update).format(error_message=str(e)))
         return SHOW_TAGS
    except RuntimeError as e:
        await query.edit_message_text(get_text("error_acoustid_ffmpeg_missing", context, update).format(error_message=str(e)))
        return SHOW_TAGS
    except Exception as e:
         await query.edit_message_text(get_text("error_acoustid_generic", context, update).format(error_message=str(e)))
         print(f"AcoustID processing error: {e}")
         return SHOW_TAGS

    if not acoustid_results:
        await query.edit_message_text(
            get_text("info_no_match_acoustid_or_error", context, update),
            reply_markup=get_edit_tags_keyboard(current_tags, file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

    potential_matches_info = []
    mb_service = None
    for result in acoustid_results:
        if 'recordings' in result and result['recordings']:
            for recording_acoustid in result['recordings']:
                mbid = recording_acoustid.get('id')
                if not mbid: continue
                title_approx = recording_acoustid.get('title', get_text("tag_value_not_available", context, update))
                artist_approx_list = [a.get('name', get_text("tag_value_not_available", context, update)) for a in recording_acoustid.get('artists', [])]
                artist_approx = ", ".join(artist_approx_list) if artist_approx_list else get_text("tag_value_not_available", context, update)
                match_info = {'mbid': mbid, 'title': title_approx, 'artist': artist_approx, 'score': result.get('score', 0)}
                potential_matches_info.append(match_info)
                if len(potential_matches_info) >= 3: break
        if len(potential_matches_info) >= 3: break

    if not potential_matches_info:
        await query.edit_message_text(
            get_text("error_acoustid_matches_no_details", context, update),
            reply_markup=get_edit_tags_keyboard(current_tags, file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

    buttons = []
    for i, match in enumerate(potential_matches_info):
        score_percent = match['score'] * 100
        button_text = f"{match['title']} by {match['artist']} ({score_percent:.0f}%)"
        context.user_data[f"acoustid_match_{i}"] = match
        buttons.append([InlineKeyboardButton(button_text[:64], callback_data=f"acoustid_select_{i}")])

    buttons.append([InlineKeyboardButton(get_text("button_cancel_acoustid_match", context, update), callback_data="acoustid_cancel_match")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(get_text("prompt_select_match_acoustid_musicbrainz", context, update), reply_markup=reply_markup)
    return AWAIT_ACOUSTID_SELECTION

async def handle_acoustid_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selection_parts = query.data.split('_')
    result_key_index = selection_parts[2]
    selected_match_info = context.user_data.pop(f"acoustid_match_{result_key_index}", None)
    for i in range(3): context.user_data.pop(f"acoustid_match_{i}", None)

    if not selected_match_info or 'mbid' not in selected_match_info:
        await query.edit_message_text(get_text("error_could_not_retrieve_selection", context, update))
        edit_ctx_fallback = context.user_data.get(EDIT_CONTEXT_KEY, {'tags': {}})
        reply_target = query.message if query.message else update.effective_message
        await reply_target.reply_text(
            get_text("info_returning_to_tag_editor", context, update),
            reply_markup=get_edit_tags_keyboard(edit_ctx_fallback.get('tags',{}), file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS

    final_tags_to_apply = {'title': selected_match_info.get('title'), 'artist': selected_match_info.get('artist')}
    mb_service = None
    try:
        mb_service = MusicBrainzService()
        if mb_service and final_tags_to_apply['title'] and final_tags_to_apply['artist']:
            mb_search_results = mb_service.search_track(artist_name=final_tags_to_apply['artist'], track_title=final_tags_to_apply['title'], limit=1)
            if mb_search_results:
                final_tags_to_apply['album'] = mb_search_results[0].get('album')
                final_tags_to_apply['year'] = mb_search_results[0].get('year')
    except ValueError as e:
         await query.edit_message_text(get_text("error_musicbrainz_service", context, update).format(error_message=str(e)))
    except Exception as e:
         await query.edit_message_text(get_text("error_fetching_mb_details_for_acoustid", context, update).format(error_message=str(e)))
         print(f"MusicBrainz detail fetch error for AcoustID: {e}")

    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx:
        await query.edit_message_text(get_text("error_critical_editing_context_lost", context, update))
        return ConversationHandler.END

    if final_tags_to_apply.get('title'): edit_ctx['tags']['title'] = final_tags_to_apply['title']
    if final_tags_to_apply.get('artist'): edit_ctx['tags']['artist'] = final_tags_to_apply['artist']
    if final_tags_to_apply.get('album'): edit_ctx['tags']['album'] = final_tags_to_apply['album']
    if final_tags_to_apply.get('year'): edit_ctx['tags']['year'] = final_tags_to_apply['year']

    await query.edit_message_text(
        get_text("info_tags_updated_from_acoustid_musicbrainz", context, update),
        reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
    )
    return SHOW_TAGS

async def handle_acoustid_cancel_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    for i in range(3): context.user_data.pop(f"acoustid_match_{i}", None)
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY, {'tags': {}})
    await query.edit_message_text(
        get_text("info_acoustid_matching_cancelled_returning_to_editor", context, update),
        reply_markup=get_edit_tags_keyboard(edit_ctx.get('tags',{}), file_loaded=True, context=context, update=update)
    )
    return SHOW_TAGS

async def search_lyrics_genius_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(get_text("info_searching_lyrics_genius", context, update))
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if not edit_ctx or 'tags' not in edit_ctx:
        print("search_lyrics_genius_handler: edit_ctx or tags not found")
        text_error = get_text("error_cannot_determine_song_details_restart", context, update)
        if query.message: await query.message.reply_text(text_error)
        else: await context.bot.send_message(chat_id=update.effective_chat.id, text=text_error)
        return
    current_tags = edit_ctx.get('tags', {})
    title = current_tags.get('title')
    artist = current_tags.get('artist')
    if not title or not artist:
        text_error = get_text("error_need_title_and_artist_for_lyrics", context, update)
        if query.message: await query.message.reply_text(text_error)
        else: await context.bot.send_message(chat_id=update.effective_chat.id, text=text_error)
        return
    try:
        genius_service = GeniusService()
        lyrics = genius_service.search_lyrics(title=title, artist=artist)
    except ValueError as e:
        text_error = get_text("error_genius_service", context, update).format(error_message=str(e))
        if query.message: await query.message.reply_text(text_error)
        else: await context.bot.send_message(chat_id=update.effective_chat.id, text=text_error)
        return
    except Exception as e:
        text_error = get_text("error_searching_genius", context, update).format(error_message=str(e))
        if query.message: await query.message.reply_text(text_error)
        else: await context.bot.send_message(chat_id=update.effective_chat.id, text=text_error)
        print(f"Genius search error: {e}")
        return

    reply_target_message = query.message if query.message else update.effective_message # Should usually be query.message
    chat_id_to_use = update.effective_chat.id # Ensure we use the correct chat ID

    if lyrics:
        header_text = get_text("header_lyrics_for_song_artist", context, update).format(song_title=title, song_artist=artist)
        if len(lyrics) + len(header_text) > 4050: # Check combined length with some buffer
            await reply_target_message.reply_text(header_text, chat_id=chat_id_to_use)
            for i in range(0, len(lyrics), 4000): # Send lyrics in chunks
                await context.bot.send_message(chat_id=chat_id_to_use, text=lyrics[i:i+4000])
        else:
            await reply_target_message.reply_text(f"{header_text}\n\n{lyrics}", chat_id=chat_id_to_use)
    else:
        await reply_target_message.reply_text(get_text("info_no_lyrics_found_genius", context, update).format(song_title=title, song_artist=artist), chat_id=chat_id_to_use)
    return

async def unhandled_callback_in_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(get_text("info_action_not_implemented_or_unavailable", context, update))
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if edit_ctx and 'tags' in edit_ctx and 'file_path' in edit_ctx and os.path.exists(edit_ctx['file_path']):
        await query.message.reply_text(
            text=get_text("text_current_tags", context, update),
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS
    await query.message.reply_text(get_text("error_session_ended_send_audio_again", context, update))
    return ConversationHandler.END

async def unhandled_command_in_conv_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text("error_unknown_command_during_edit", context, update))
    edit_ctx = context.user_data.get(EDIT_CONTEXT_KEY)
    if edit_ctx and 'tags' in edit_ctx and 'file_path' in edit_ctx and os.path.exists(edit_ctx['file_path']):
        await update.message.reply_text(
            text=get_text("text_current_tags", context, update),
            reply_markup=get_edit_tags_keyboard(edit_ctx['tags'], file_loaded=True, context=context, update=update)
        )
        return SHOW_TAGS
    return ConversationHandler.END

def setup_music_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.AUDIO, handle_music_file)],
        states={
            SHOW_TAGS: [
                CallbackQueryHandler(prompt_edit_tag, pattern="^edit_tag_(title|artist|album|year|genre|tracknumber)$"),
                CallbackQueryHandler(prompt_edit_album_art, pattern="^edit_tag_album_art$"),
                CallbackQueryHandler(save_tags_handler, pattern="^save_tags$"),
                CallbackQueryHandler(auto_fill_musicbrainz_handler, pattern="^auto_fill_musicbrainz$"),
                CallbackQueryHandler(match_acoustid_handler, pattern="^match_acoustid$"),
                CallbackQueryHandler(search_lyrics_genius_handler, pattern="^search_lyrics_genius$"),
                CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
                CallbackQueryHandler(unhandled_callback_in_conv, pattern="^.*$"),
            ],
            AWAIT_NEW_TAG_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_tag_value),
                CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
                CommandHandler('cancel', cancel_edit_tags),
            ],
            AWAIT_ALBUM_ART: [
                MessageHandler(filters.PHOTO, save_new_album_art),
                CommandHandler('cancel', cancel_edit_tags),
                CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: u.message.reply_text(get_text("error_not_an_image_send_photo_or_cancel", c, u))), # Pass u,c for get_text
            ],
            AWAIT_MB_SELECTION: [
                CallbackQueryHandler(handle_mb_selection, pattern="^mb_select_"),
                CallbackQueryHandler(handle_mb_cancel_autofill, pattern="^mb_cancel_autofill$"),
                CallbackQueryHandler(unhandled_callback_in_conv, pattern="^.*$"),
            ],
            AWAIT_ACOUSTID_SELECTION: [
                CallbackQueryHandler(handle_acoustid_selection, pattern="^acoustid_select_"),
                CallbackQueryHandler(handle_acoustid_cancel_match, pattern="^acoustid_cancel_match$"),
                CallbackQueryHandler(unhandled_callback_in_conv, pattern="^.*$"),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_edit_tags),
            CallbackQueryHandler(cancel_edit_tags, pattern="^cancel_edit_tags$"),
            MessageHandler(filters.COMMAND | filters.TEXT, unhandled_command_in_conv_fallback)
        ],
        allow_reentry=True
    )
    application.add_handler(conv_handler)