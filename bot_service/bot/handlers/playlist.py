#local playlist.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from ..services.spotify import create_playlist, create_playlist_from_song,sp, create_playlist_from_genre
from spotify_service.spotify.cache import cached_get_recommendations
from logging_config import setup_logging
from database_service.database.crud import create_playlist_for_database, get_user, create_playlist_tracks_bulk, update_playlist_track_count
import asyncio
from database_service.database import get_db
from ..utils.language import get_text
from config import SPOTIFY_USERNAME
logger = setup_logging(logstash_host='localhost', logstash_port=5000)

async def create_playlist_from_inline(update: Update, context: CallbackContext) -> None:
    chosen_result = update.chosen_inline_result
    result_id, item_id = chosen_result.result_id.split('_', 1)
    keyboard = [
        [InlineKeyboardButton("50 tracks", callback_data=f"50_{result_id}_{item_id}"),
         InlineKeyboardButton("100 tracks", callback_data=f"100_{result_id}_{item_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_user.id, 
                                   text='How many tracks do you want in your playlist?', 
                                   reply_markup=reply_markup)
async def create_playlist_async(name, tracks):
    try:
        playlist = await asyncio.to_thread(sp.user_playlist_create, SPOTIFY_USERNAME, name, public=True, description="Created by @AR_MUSICLAND_BOT")
        await asyncio.to_thread(sp.playlist_add_items, playlist['id'], tracks)
        logger.info(f"Playlist successfully created: {playlist['external_urls']['spotify']}")
        return playlist['external_urls']['spotify']
    except Exception as e:
        logger.error(f"Error in create_playlist_async: {str(e)}")
        raise
async def create_playlist_with_count(update: Update, context: CallbackContext, track_count: int, callback_data: str):
    data_type, data_id = callback_data.split('_', 1)
    try:
        db = next(get_db())
        user = await asyncio.to_thread(get_user, db, update.effective_user.id)
        
        if data_type == 'mood':
            mood = data_id
            results = sp.search(q=mood, type='track', limit=5)
            seed_tracks = [track['id'] for track in results['tracks']['items'][:5]]
            recommendations = await cached_get_recommendations(','.join(seed_tracks), limit=track_count)
            track_uris = [track['uri'] for track in recommendations['tracks']]
            playlist_name = f"{mood.capitalize()} Mood Playlist ({track_count} tracks)"
        elif data_type == 'genre':
            genre = data_id
            track_uris = await create_playlist_from_genre(genre, target_count=track_count)
            playlist_name = f"{genre.capitalize()} Genre Playlist ({track_count} tracks)"
        elif data_type in ['song', 'track']:
            track_uris = await create_playlist_from_song(data_id, target_count=track_count)
            track = sp.track(data_id)
            playlist_name = f"Playlist inspired by {track['name']} ({track_count} tracks)"
        elif data_type == 'artist':
            artist = sp.artist(data_id)
            recommendations = sp.recommendations(seed_artists=[data_id], limit=track_count)
            track_uris = [track['uri'] for track in recommendations['tracks']]
            playlist_name = f"Playlist inspired by {artist['name']} ({track_count} tracks)"
        
        playlist_link = await create_playlist_async(playlist_name, track_uris)
        
        db_playlist = await asyncio.to_thread(create_playlist_for_database, db, user.id, playlist_link, playlist_name, f"Created by @AR_MUSICLAND_BOT", created_by=user.username, mood=mood if data_type == 'mood' else None)
        # Fetch track details in bulk
        tracks_info = await asyncio.to_thread(sp.tracks, [uri.split(':')[-1] for uri in track_uris])
        logger.debug(f"Tracks info: {tracks_info}")
        
        # Prepare bulk insert data with error handling
        tracks_data = []
        for track in tracks_info['tracks']:
            try:
                tracks_data.append({
                    'playlist_id': db_playlist.spotify_playlist_id,
                    'spotify_track_id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown Artist',
                    'album': track['album']['name'] if track['album'] else 'Unknown Album',
                    'duration_ms': track['duration_ms']
                })
            except (KeyError, TypeError, IndexError) as e:
                logger.warning(f"Error processing track: {str(e)}")
                continue
        
        # Bulk insert tracks
        await asyncio.to_thread(create_playlist_tracks_bulk, db, tracks_data)
        
        # Update playlist track count
        await asyncio.to_thread(update_playlist_track_count, db, db_playlist.spotify_playlist_id, len(tracks_data))
        
        response = get_text(context, 'playlist_created').format(playlist_name, playlist_link)

        keyboard = [
            [InlineKeyboardButton("Create Another Playlist", callback_data=f"create_playlist_{data_type}_{data_id}")],
            [InlineKeyboardButton("Explore More Music", callback_data='menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text=response, reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Error creating playlist: {str(e)}", exc_info=True)
        response = "Oops! We encountered an issue while crafting your perfect playlist. Let's try again!"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data='menu')]])
        await update.callback_query.edit_message_text(text=response, reply_markup=reply_markup)