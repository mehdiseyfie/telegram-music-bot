# 🎵 Telegram Music Bot

A powerful Telegram bot that creates personalized music playlists using the Spotify API, with data persistence through MySQL and Redis caching for optimal performance.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Latest-blue.svg)](https://core.telegram.org/bots/api)
[![Spotify API](https://img.shields.io/badge/Spotify%20API-v1-green.svg)](https://developer.spotify.com/documentation/web-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎼 **Personalized Playlists**: Create custom playlists based on user preferences
- 🔍 **Smart Search**: Search for songs, artists, and albums using Spotify's extensive catalog
- 💾 **Data Persistence**: User preferences and playlists stored in MySQL database
- ⚡ **Fast Performance**: Redis caching for quick response times
- 🔐 **User Authentication**: Secure Spotify OAuth integration
- 📊 **Music Recommendations**: Get personalized music suggestions
- 🎨 **Rich Media**: Display album artwork and track information
- 🌐 **Multi-user Support**: Handle multiple users simultaneously

## 🛠️ Tech Stack

- **Language**: Python 3.8+
- **Bot Framework**: python-telegram-bot / aiogram
- **Music API**: Spotify Web API
- **Database**: MySQL
- **Cache**: Redis
- **Authentication**: OAuth 2.0

## 📋 Prerequisites

Before running this bot, ensure you have the following installed:

- Python 3.8 or higher
- MySQL Server
- Redis Server
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Spotify Developer Account

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mehdiseyfie/telegram-music-bot.git
cd telegram-music-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MySQL Database

```bash
# Log into MySQL
mysql -u root -p

# Create database
CREATE DATABASE telegram_music_bot;

# Import schema (if schema.sql is provided)
mysql -u root -p telegram_music_bot < schema.sql
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Spotify API Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=telegram_music_bot

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
```

### 6. Obtain API Credentials

#### Telegram Bot Token:
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the provided token

#### Spotify API Credentials:
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in and create a new app
3. Copy the Client ID and Client Secret
4. Add redirect URI in app settings

## 🎮 Usage

### Start the Bot

```bash
python main.py
```

### Bot Commands

- `/start` - Initialize the bot and get welcome message
- `/help` - Display available commands and features
- `/login` - Connect your Spotify account
- `/search [query]` - Search for songs, artists, or albums
- `/playlist` - View your saved playlists
- `/create` - Create a new playlist
- `/recommend` - Get personalized music recommendations
- `/trending` - View trending tracks
- `/settings` - Configure bot preferences
- `/logout` - Disconnect Spotify account

### Example Usage

```
User: /search Bohemian Rhapsody
Bot: 🔍 Found results for "Bohemian Rhapsody"
     1. Bohemian Rhapsody - Queen
     2. Bohemian Rhapsody - Panic! At The Disco
     ...

User: /create Summer Vibes
Bot: ✨ Creating playlist "Summer Vibes"...
     Playlist created successfully!
```

## 📁 Project Structure

```
telegram-music-bot/
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── search.py
│   │   ├── playlist.py
│   │   └── auth.py
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline_keyboards.py
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py
│       └── validators.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── connection.py
│   └── queries.py
├── services/
│   ├── __init__.py
│   ├── spotify_service.py
│   ├── redis_service.py
│   └── recommendation_engine.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── logs/
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py
│   └── test_services.py
├── .env.example
├── .gitignore
├── requirements.txt
├── schema.sql
├── main.py
├── README.md
└── LICENSE
```

## 🔧 Configuration

### Redis Cache Settings

The bot uses Redis to cache frequently accessed data:
- Spotify search results (TTL: 1 hour)
- User session data (TTL: 24 hours)
- Track metadata (TTL: 7 days)

### Database Schema

Main tables:
- `users` - User information and Spotify tokens
- `playlists` - User-created playlists
- `tracks` - Cached track information
- `user_preferences` - User music preferences

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file: .env
    depends_on:
      - mysql
      - redis
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: telegram_music_bot
      MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot --cov-report=html

# Run specific test file
pytest tests/test_handlers.py
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code follows PEP 8 style guidelines and includes appropriate tests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Spotipy](https://github.com/plamere/spotipy) - Spotify Web API wrapper
- [MySQL](https://www.mysql.com/) - Database management
- [Redis](https://redis.io/) - In-memory data structure store

## 📧 Contact

Mehdi Seyfie - [@mehdiseyfie](https://github.com/mehdiseyfie)

Project Link: [https://github.com/mehdiseyfie/telegram-music-bot](https://github.com/mehdiseyfie/telegram-music-bot)

## 🐛 Bug Reports & Feature Requests

If you encounter any bugs or have feature requests, please [open an issue](https://github.com/mehdiseyfie/telegram-music-bot/issues) on GitHub.

---

**⭐ If you find this project useful, please consider giving it a star!**
