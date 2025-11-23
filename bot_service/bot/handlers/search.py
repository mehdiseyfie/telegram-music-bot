from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import CallbackContext, ContextTypes
from telegram.error import BadRequest
from ..utils.helpers import check_membership
from logging_config import setup_logging
from spotify_service.spotify.cache import cached_spotify_search
from ..utils.language import get_text
import asyncio

logger = setup_logging(logstash_host='localhost', logstash_port=5000)

async def genre_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("To search for a genre, type '@AR_MUSICLAND_BOT genre:' followed by the genre name in any chat. For example: @AR_MUSICLAND_BOT genre: rock")

async def mood_command(update: Update, context: CallbackContext) -> None:
    moods = ["Happy", "Sad", "Energetic", "Calm", "Romantic", "Angry"]
    keyboard = [[InlineKeyboardButton(mood, callback_data=f'mood_{mood.lower()}')] for mood in moods]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = "Please choose a mood:"
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)

async def artist_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("To search for an artist, type '@AR_MUSICLAND_BOT art:' followed by the artist name in any chat. For example: @AR_MUSICLAND_BOT art: Ed Sheeran")

async def song_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("To search for a song, type '@AR_MUSICLAND_BOT son:' followed by the song name in any chat. For example: @AR_MUSICLAND_BOT son: Shape of You")

async def inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return
    
    try:
        is_member = await check_membership(update, context)
        if not is_member:
            results = [
                InlineQueryResultArticle(
                    id="join_channel",
                    title=get_text(context, 'join_channel_title'),
                    description=get_text(context, 'join_channel_description'),
                    input_message_content=InputTextMessageContent(get_text(context, 'join_channel_message'))
                )
            ]
            await update.inline_query.answer(results, cache_time=1)
            return
        
        results = []
        
        if query.startswith("son:"):
            track_query = query[4:].strip()
            if track_query:
                track_results = await cached_spotify_search(track_query, 'track', 10)
                results = [
                    InlineQueryResultArticle(
                        id=f"track_{track['id']}",
                        title=track['name'],
                        description=f"Artist: {track['artists'][0]['name']}",
                        thumbnail_url=track['album']['images'][0]['url'] if track['album']['images'] else None,
                        input_message_content=InputTextMessageContent(f"Track: {track['name']} by {track['artists'][0]['name']}\nSpotify URI: {track['uri']}"),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(context, 'create_playlist'), callback_data=f"create_playlist_song_{track['id']}")]])
                    )
                    for track in track_results['tracks']['items']
                ]
        elif query.startswith("art:"):
            artist_query = query[4:].strip()
            if artist_query:
                artist_results = await cached_spotify_search(artist_query, 'artist', 10)
                results = [
                    InlineQueryResultArticle(
                        id=f"artist_{artist['id']}",
                        title=f"Artist: {artist['name']}",
                        description=f"Followers: {artist['followers']['total']}",
                        thumbnail_url=artist['images'][0]['url'] if artist['images'] else None,
                        input_message_content=InputTextMessageContent(f"Artist: {artist['name']}\nSpotify URI: {artist['uri']}"),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(context, 'create_playlist'), callback_data=f"create_playlist_artist_{artist['id']}")]])
                    )
                    for artist in artist_results['artists']['items']
                ]
        elif query.startswith("genre:"):
            from .start import SPOTIFY_GENRES
            genre_query = query[6:].strip().lower()
            filtered_genres = [genre for genre in SPOTIFY_GENRES if genre_query in genre.lower()]
            
            results = [
                InlineQueryResultArticle(
                    id=f"genre_{i}",
                    title=genre.capitalize(),
                    description=get_text(context, 'create_playlist_for_genre').format(genre),
                    input_message_content=InputTextMessageContent(get_text(context, 'create_playlist_for_genre_message').format(genre.capitalize())),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(context, 'create_playlist'), callback_data=f"create_playlist_genre_{genre}")]])
                )
                for i, genre in enumerate(filtered_genres[:50])  # Limit to 50 results as per Telegram's limit
            ]
        
    except Exception as e:
        logger.error(f"Error in inline search: {str(e)}", exc_info=True)
        results = [
            InlineQueryResultArticle(
                id="error",
                title=get_text(context, 'error_occurred'),
                description=get_text(context, 'try_again_later'),
                input_message_content=InputTextMessageContent(get_text(context, 'error_message'))
            )
        ]
    
    try:
        await update.inline_query.answer(results, cache_time=300)  # Cache results for 5 minutes
    except BadRequest as e:
        if "Query is too old" in str(e):
            logger.warning(f"Inline query timed out: {e}")
            error_result = [InlineQueryResultArticle(
                id='timeout_error',
                title="Search timed out",
                input_message_content=InputTextMessageContent("The search request timed out. Please try again.")
            )]
    try:
        await query.answer()
    except BadRequest as e:
        if "Query is too old" in str(e):
            logger.warning(f"Callback query timed out: {e}")
            # Optionally, send a new message to the user
            await update.effective_chat.send_message("Sorry, this action has expired. Please try again.")
        else:
            # Handle other BadRequest errors
            logger.error(f"Error answering callback query: {e}")
    except asyncio.TimeoutError:
        logger.error("Timeout occurred while answering inline query")
    except Exception as e:
        logger.error(f"Unexpected error in inline search: {e}")