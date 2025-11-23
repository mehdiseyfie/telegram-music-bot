# 🎵 Telegram Music Playlist Bot

A **Telegram bot** that lets users create personalized music playlists using the **Spotify API**. Optimized to handle **100,000+ concurrent users**, this bot provides playlist recommendations based on **mood, genre, or favorite tracks/artists**.

---

## ✨ Features

* 🎶 Create playlists by **mood**, **genre**, or **artist/track inspiration**
* ⚡ Fetch recommendations from Spotify API
* 🗄 Store user & playlist data in **MySQL**
* 🚀 Cache recommendations in **Redis** for fast performance
* 🤖 Interactive Telegram commands & inline buttons

---

## 🛠 Tech Stack

* **Python** with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
* **MySQL** for database
* **Redis** for caching
* **Spotify API** for music recommendations

---

## ⚙️ Setup Instructions

1. **Clone the repository:**

```bash
git clone https://github.com/mehdiseyfie/telegram-music-bot.git
cd my-project
```

2. **Create a virtual environment:**

```bash
python -m venv myenv
source myenv/bin/activate   # Linux/macOS
myenv\Scripts\activate      # Windows
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables in `.env`:**

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_redirect_uri
MYSQL_HOST=localhost
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_DATABASE=your_db_name
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

5. **Run the bot:**

```bash
python bot.py
```

---

## 🤝 Contributing

Contributions are welcome! Open an issue or submit a pull request for new features or bug fixes.

---

## 📄 License

MIT License
