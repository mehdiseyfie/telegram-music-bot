from telegram.ext import CallbackContext

LANGS = {
    'en': {
        'welcome': "🎵 *Welcome {}!* 🎵\n\nWelcome to your personal music bot. Ready to dive into the world of music?",
        'main_menu': "🚀 *Main Menu*\n\nHow would you like to explore music today? Choose one of the options below:",
        'discover_songs': "🎵 Discover Songs",
        'explore_artists': "🎤 Explore Artists",
        'playlist_by_mood': "😊 Playlist by Mood",
        'dive_into_genres': "🎸 Dive into Genres",
        'help': "❓ Help",
        'my_profile': "👤 My Profile",
        'change_language': "🌐 Change Language",
        'back_to_menu': "🔙 Back to Main Menu",
        'language_menu': "🌐 *Language Selection*\n\nPlease select your preferred language:",
        'english': "🇬🇧 English",
        'persian': "🇮🇷 Persian",
        'join_channel': "Join Channel",
        'join_channel_message': "Please join our channel to use this bot:",
        'check_membership': "Check Membership",
        'check_membership_message': "Please check if you've joined our channel:",
        'search_song_text': "Click the button below to search for a song:",
        'search_artist_text': "Click the button below to search for an artist:",
        'search_genre_text': "Click the button below to search for a genre:",
        'search_song': "Search Song",
        'search_artist': "Search Artist",
        'search_genre': "Search Genre",
        'ask_track_count': "How many tracks do you want in your playlist?",
        'song_search_instructions': "To search for a song, type '@AR_MUSICLAND_BOT trk:' followed by the song name in any chat.",
        'artist_search_instructions': "To search for an artist, type '@AR_MUSICLAND_BOT art:' followed by the artist name in any chat.",
        'genre_search_instructions': "To search for a genre, type '@AR_MUSICLAND_BOT genre:' followed by the genre name in any chat.",
        'select_genre': 'Please select a genre:',
        'create_playlist': "Create Another Playlist",
        'explore_more_music': "Explore More Music",
        'playlist_created': "Your personalized playlist '{}' has been created with high precision! 🎉\nEnjoy your music here: {}",
        'playlist_creation_error': "Oops! We encountered an issue while crafting your perfect playlist. Let's try again!"
    },
    
    'fa': {
        'welcome': "🎵 *{} خوش آمدید!* 🎵\n\nبه ربات موسیقی شخصی خود خوش آمدید. آماده‌اید تا در دنیای موسیقی غرق شوید؟",
        'main_menu': "🚀 *منوی اصلی*\n\nچطور می‌خواهید امروز به کشف موسیقی بپردازید؟ یکی از گزینه‌های زیر را انتخاب کنید:",
        'discover_songs': "🎵 کشف آهنگ‌ها",
        'explore_artists': "🎤 جستجوی هنرمندان",
        'playlist_by_mood': "😊 پلی‌لیست بر اساس حال و هوا",
        'dive_into_genres': "🎸 کاوش در ژانرها",
        'help': "❓ راهنما",
        'my_profile': "👤 پروفایل من",
        'change_language': "🌐 تغییر زبان",
        'back_to_menu': "🔙 بازگشت به منوی اصلی",
        'language_menu': "🌐 *انتخاب زبان*\n\nلطفاً زبان مورد نظر خود را انتخاب کنید:",
        'english': "🇬🇧 انگلیسی",
        'persian': "🇮🇷 فارسی",
        'join_channel': "عضویت در کانال",
        'join_channel_message': "لطفاً برای استفاده از این ربات در کانال ما عضو شوید:",
        'check_membership': "بررسی عضویت",
        'check_membership_message': "لطفاً بررسی کنید که آیا در کانال ما عضو شده‌اید:",
        'search_song_text': "برای جستجوی یک آهنگ، روی دکمه زیر کلیک کنید:",
        'search_artist_text': "برای جستجوی یک هنرمند، روی دکمه زیر کلیک کنید:",
        'search_genre_text': "برای جستجوی یک ژانر، روی دکمه زیر کلیک کنید:",
        'search_song': "جستجوی آهنگ",
        'search_artist': "جستجوی هنرمند",
        'search_genre': "جستجوی ژانر",
        'ask_track_count': "چند آهنگ می‌خواهید در پلی‌لیست خود داشته باشید؟",
        'song_search_instructions': "برای جستجوی یک آهنگ، '@AR_MUSICLAND_BOT trk:' را تایپ کرده و سپس نام آهنگ را در هر چتی وارد کنید.",
        'artist_search_instructions': "برای جستجوی یک هنرمند، '@AR_MUSICLAND_BOT art:' را تایپ کرده و سپس نام هنرمند را در هر چتی وارد کنید.",
        'genre_search_instructions': "برای جستجوی یک ژانر، '@AR_MUSICLAND_BOT genre:' را تایپ کرده و سپس نام ژانر را در هر چتی وارد کنید.",
        'select_genre':"لطفاً یک ژانر را انتخاب کنید",
        'create_playlist': "ایجاد پلی‌لیست دیگر",
        'explore_more_music': "کاوش موسیقی بیشتر",
        'playlist_created': "پلی‌لیست شخصی‌سازی شده شما با نام '{}' با دقت بالا ایجاد شد! 🎉\nموسیقی خود را اینجا گوش دهید: {}",
        'playlist_creation_error': "اوه! در ساخت پلی‌لیست دلخواه شما مشکلی پیش آمد. دوباره امتحان کنیم!"
    }
}

def get_user_language(context):
    if isinstance(context, dict):
        return context.get('language', 'en')
    elif hasattr(context, 'user_data'):
        return context.user_data.get('language', 'en')
    else:
        return 'en'

def set_user_language(context: CallbackContext, language: str):
    context.user_data['language'] = language

def get_text(context, key: str) -> str:
    if isinstance(context, dict):
        lang = context.get('language', 'en')
    elif hasattr(context, 'user_data'):
        lang = context.user_data.get('language', 'en')
    else:
        lang = 'en'
    
    try:
        return LANGS[lang][key]
    except KeyError:
        # If the key doesn't exist in the selected language, try English
        try:
            return LANGS['en'][key]
        except KeyError:
            # If the key doesn't exist in English either, return a default message
            return f"Missing text for key: {key}"