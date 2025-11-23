#start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, CallbackContext
from ..utils.helpers import check_membership, force_subscription
from logging_config import setup_logging
from .search import mood_command
from ..utils.language import get_text, set_user_language
from .playlist import create_playlist_with_count
from database_service.database import get_db
from database_service.database.crud import get_user, create_user, update_user_language
import asyncio
import math
from cachetools import TTLCache, cached
from functools import lru_cache
from telegram.ext import InlineQueryHandler
from telegram import InlineQuery


logger = setup_logging(logstash_host='localhost', logstash_port=5000)

# Use in-memory cache for frequently accessed data
user_cache = TTLCache(maxsize=10000, ttl=3600)  # Cache user data for 1 hour
language_cache = TTLCache(maxsize=10000, ttl=3600)  # Cache language data for 1 hour

@cached(cache=user_cache)
async def get_cached_user(user_id: int):
    db = next(get_db())
    user = await asyncio.to_thread(get_user, db, user_id)
    return user
@cached(cache=language_cache)
async def get_cached_language(user_id: int):
    user = await get_cached_user(user_id)
    return user.language if user else 'en'

@lru_cache(maxsize=1000)
def get_cached_text(language: str, key: str):
    return get_text({'language': language}, key)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await force_subscription(update, context):
        return

    user = update.effective_user
    user_id = user.id

    if user_id in context.user_data:
        db_user = context.user_data[user_id]
    else:
        db_user = await get_cached_user(user_id)
        context.user_data[user_id] = db_user

    if not db_user:
        db = next(get_db())
        db_user = await asyncio.to_thread(create_user, db, user_id, user.username)
        language = 'fa'  # تغییر زبان پیش‌فرض به فارسی
    else:
        language = db_user.language

    context.user_data['language'] = language

    if not language:
        await show_language_menu(update, context)
    else:
        await show_main_menu(update, context)
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_language_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await force_subscription(update, context):
        return
    logger.info("Showing main menu")
    language = context.user_data.get('language', 'en')
    keyboard = [
        [InlineKeyboardButton(get_cached_text(language, 'discover_songs'), callback_data='song')],
        [InlineKeyboardButton(get_cached_text(language, 'explore_artists'), callback_data='artist')],
        [InlineKeyboardButton(get_cached_text(language, 'playlist_by_mood'), callback_data='mood')],
        [InlineKeyboardButton(get_cached_text(language, 'dive_into_genres'), callback_data='genre')],
        [InlineKeyboardButton(get_cached_text(language, 'change_language'), callback_data='change_language')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = get_cached_text(language, 'main_menu')
    if update.callback_query:
        await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)

async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
         InlineKeyboardButton("🇮🇷 فارسی", callback_data='lang_fa')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text="Please select your language / لطفا زبان خود را انتخاب کنید", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text="Please select your language / لطفا زبان خود را انتخاب کنید", reply_markup=reply_markup)

async def explore_more_music(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Discover Songs", callback_data='song')],
        [InlineKeyboardButton("Explore Artists", callback_data='artist')],
        [InlineKeyboardButton("Playlist by Mood", callback_data='mood')],
        [InlineKeyboardButton("Dive into Genres", callback_data='genre')],
        [InlineKeyboardButton("Back to Main Menu", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("How would you like to explore more music?", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "check_join_status":
        from ..utils.helpers import handle_subscription_check
        is_member = await handle_subscription_check(update, context)
        if is_member:
            await show_main_menu(update, context)
        return
    
    if not await force_subscription(update, context):
        return
    
    if query.data.startswith('lang_'):
        language = query.data.split('_')[1]
        db = next(get_db())
        await asyncio.to_thread(update_user_language, db, query.from_user.id, language)
        context.user_data['language'] = language
        user_cache.pop(query.from_user.id, None)  # Clear the user cache
        language_cache.pop(query.from_user.id, None)  # Clear the language cache
        await show_main_menu(update, context)
        
    elif query.data == 'mood':
        await mood_command(update, context)
        
    elif query.data.startswith('mood_'):
        mood = query.data.split('_')[1]
        await ask_track_count(update, context, f"mood_{mood}")
        
    elif query.data.startswith(('50_', '100_')):
        parts = query.data.split('_')
        count = int(parts[0])
        data_type = parts[1]
        item_id = '_'.join(parts[2:])
        await create_playlist_with_count(update, context, count, f"{data_type}_{item_id}")
    elif query.data == 'change_language':
        await show_language_menu(update, context)
    elif query.data == 'menu':
        await show_main_menu(update, context)
    elif query.data == 'explore_more':
        await explore_more_music(update, context)
    elif query.data in ['song', 'artist', 'mood']:
        await handle_main_menu_selection(update, context, query.data)
    elif query.data.startswith('create_playlist_'):
        parts = query.data.split('_')
        data_type = parts[2]
        item_id = '_'.join(parts[3:])
        await ask_track_count(update, context, f"{data_type}_{item_id}")
    elif query.data == 'genre':
        await show_genre_buttons(update, context)
    elif query.data.startswith('genre_page_'):
        page = int(query.data.split('_')[-1])
        await show_genre_buttons(update, context, page=page)
    elif query.data.startswith('genre_'):
        genre = query.data.split('_')[1]
        await ask_track_count(update, context, f"genre_{genre}")
    else:
        await show_main_menu(update, context)
        
SPOTIFY_GENRES = [
    "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime", "black-metal",
    "bluegrass", "blues", "bossanova", "brazil", "breakbeat", "british", "cantopop",
    "chicago-house", "children", "chill", "classical", "club", "comedy", "country",
    "dance", "dancehall", "death-metal", "deep-house", "detroit-techno", "disco", "disney",
    "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk",
    "forro", "french", "funk", "garage", "german", "gospel", "goth", "grindcore", "groove",
    "grunge", "guitar", "happy", "hard-rock", "hardcore", "hardstyle", "heavy-metal",
    "hip-hop", "holidays", "honky-tonk", "house", "idm", "indian", "indie", "indie-pop",
    "industrial", "iranian", "j-dance", "j-idol", "j-pop", "j-rock", "jazz", "k-pop", "kids",
    "latin", "latino", "malay", "mandopop", "metal", "metal-misc", "metalcore",
    "minimal-techno", "movies", "mpb", "new-age", "new-release", "opera", "pagode",
    "party", "philippines-opm", "piano", "pop", "pop-film", "post-dubstep", "power-pop",
    "progressive-house", "psych-rock", "punk", "punk-rock", "r-n-b", "rainy-day", "reggae",
    "reggaeton", "road-trip", "rock", "rock-n-roll", "rockabilly", "romance", "sad", "salsa",
    "samba", "sertanejo", "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter",
    "soul", "soundtracks", "spanish", "study", "summer", "swedish", "synth-pop", "tango",
    "techno", "trance", "trip-hop", "turkish", "work-out", "world-music"
]

GENRES_PER_PAGE = 15

async def show_genre_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, search_query: str = None) -> None:
    if search_query:
        filtered_genres = [genre for genre in SPOTIFY_GENRES if search_query.lower() in genre.lower()]
    else:
        filtered_genres = SPOTIFY_GENRES

    total_pages = math.ceil(len(filtered_genres) / GENRES_PER_PAGE)
    start_index = page * GENRES_PER_PAGE
    end_index = start_index + GENRES_PER_PAGE
    current_genres = filtered_genres[start_index:end_index]

    keyboard = []
    for i in range(0, len(current_genres), 3):
        row = []
        for j in range(3):
            if i + j < len(current_genres):
                genre = current_genres[i + j]
                row.append(InlineKeyboardButton(genre.capitalize(), callback_data=f'genre_{genre}'))
        keyboard.append(row)

    navigation_row = []
    if page > 0:
        navigation_row.append(InlineKeyboardButton("◀️ Previous", callback_data=f'genre_page_{page-1}'))
    if page < total_pages - 1:
        navigation_row.append(InlineKeyboardButton("Next ▶️", callback_data=f'genre_page_{page+1}'))
    if navigation_row:
        keyboard.append(navigation_row)

    keyboard.append([InlineKeyboardButton("🔍 Search Genres", switch_inline_query_current_chat="genre:")])
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = f"Select a genre or search for one (Page {page + 1}/{total_pages}):"
    if search_query:
        message_text = f"Search results for '{search_query}' (Page {page + 1}/{total_pages}):"

    if update.callback_query:
        await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)

async def handle_genre_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    inline_query = update.inline_query
    if not inline_query:
        return
    query = inline_query.query
    search_query = query.replace("genre:", "").strip()
    
    if search_query:
        filtered_genres = [genre for genre in SPOTIFY_GENRES if search_query.lower() in genre.lower()]
        results = [
            InlineQueryResultArticle(
                id=genre,
                title=genre.capitalize(),
                input_message_content=InputTextMessageContent(f"/genre {genre}")
            )
            for genre in filtered_genres[:50]  # Limit to 50 results as per Telegram's limit
        ]
    else:
        results = []

    await inline_query.answer(results)

async def handle_main_menu_selection(update: Update, context: CallbackContext, selection: str):
    if selection == 'song':
        await show_search_option(update, context, "song")
    elif selection == 'artist':
        await show_search_option(update, context, "artist")
    elif selection == 'mood':
        await mood_command(update, context)
    elif selection == 'genre':
        await show_genre_buttons(update, context)

async def show_search_option(update: Update, context: CallbackContext, search_type: str):
    text = get_text(context, f'search_{search_type}_text')
    switch_text = f"{search_type[0:3]}:"
    keyboard = [
        [InlineKeyboardButton(get_text(context, f'search_{search_type}'), switch_inline_query_current_chat=switch_text)],
        [InlineKeyboardButton(get_text(context, 'back_to_menu'), callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)

async def ask_track_count(update: Update, context: CallbackContext, callback_data):
    keyboard = [
        [InlineKeyboardButton("50 tracks", callback_data=f"50_{callback_data}"),
         InlineKeyboardButton("100 tracks", callback_data=f"100_{callback_data}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(get_text(context, 'ask_track_count'), reply_markup=reply_markup)



async def handle_message(update: Update, context: CallbackContext) -> None:
    if not await force_subscription(update, context):
        return
    if update.message is None:
        return
    user = update.effective_user
    db_user = await asyncio.to_thread(get_user, next(get_db()), user.id)

    if not db_user:
        db = next(get_db())
        user = await asyncio.to_thread(create_user, db, update.effective_user.id, update.effective_user.username)
        context.user_data['language'] = 'en'  # Default language
    else:
        if hasattr(user, 'language'):
            context.user_data['language'] = user.language
        else:
            context.user_data['language'] = 'en'  # Set a default language

    if 'language' not in context.user_data:
        await show_language_menu(update, context)
        return

    text = update.message.text
    if text.startswith("/genre"):
        search_query = text.replace("/genre", "").strip()
        await show_genre_buttons(update, context, search_query=search_query)
    elif text.startswith(("/song", "/artist", "/mood")):
        command = text[1:].split()[0]
        if command in ["song", "artist", "genre"]:
            reply_text = get_text(context, f'{command}_search_instructions')
            button_text = get_text(context, f'search_{command}')
            await update.message.reply_text(
                reply_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(button_text, switch_inline_query_current_chat=f"{command[0:3]}:")]])
            )
        elif command == "mood":
            await mood_command(update, context)

async def clean_caches():
    while True:
        user_cache.expire()
        language_cache.expire()
        await asyncio.sleep(3600)  # Clean up every hour

# Function to start the cache cleaning task
def start_cache_cleaning():
    asyncio.create_task(clean_caches())