from locust import HttpUser, task, between
import random

class TelegramBotUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:80"  # Nginx listens on port 80

    def on_start(self):
        # Simulate user joining the channel
        self.client.post("/bot", json={"callback_query": {"data": "check_membership"}})

    @task(5)
    def start_command(self):
        self.client.post("/bot", json={"message": {"text": "/start"}})

    @task(3)
    def show_main_menu(self):
        self.client.post("/bot", json={"callback_query": {"data": "menu"}})

    @task(2)
    def change_language(self):
        languages = ["lang_en", "lang_fa"]
        self.client.post("/bot", json={"callback_query": {"data": random.choice(languages)}})

    @task(3)
    def search_song(self):
        songs = ["Shape of You", "Blinding Lights", "Dance Monkey", "Watermelon Sugar"]
        self.client.post("/bot", json={"inline_query": {"query": f"son:{random.choice(songs)}"}})

    @task(3)
    def search_artist(self):
        artists = ["Ed Sheeran", "The Weeknd", "Ariana Grande", "Drake"]
        self.client.post("/bot", json={"inline_query": {"query": f"art:{random.choice(artists)}"}})

    @task(2)
    def search_genre(self):
        genres = ["rock", "pop", "hip-hop", "electronic", "jazz"]
        self.client.post("/bot", json={"inline_query": {"query": f"genre:{random.choice(genres)}"}})

    @task(2)
    def select_mood(self):
        moods = ["happy", "sad", "energetic", "calm", "romantic", "angry"]
        self.client.post("/bot", json={"callback_query": {"data": f"mood_{random.choice(moods)}"}})

    @task(1)
    def create_playlist(self):
        playlist_types = ["song", "artist", "genre", "mood"]
        counts = ["50", "100"]
        self.client.post("/bot", json={
            "callback_query": {
                "data": f"{random.choice(counts)}_{random.choice(playlist_types)}_123456"
            }
        })

    @task(1)
    def explore_genres(self):
        self.client.post("/bot", json={"callback_query": {"data": "genre"}})

    @task(1)
    def navigate_genre_pages(self):
        self.client.post("/bot", json={"callback_query": {"data": f"genre_page_{random.randint(0, 5)}"}})

    @task(2)
    def handle_text_message(self):
        messages = ["/genre rock", "/song", "/artist", "/mood"]
        self.client.post("/bot", json={"message": {"text": random.choice(messages)}})

class WebhookUser(HttpUser):
    wait_time = between(0.1, 0.5)
    host = "http://localhost:80"  # Nginx listens on port 80

    @task
    def simulate_webhook(self):
        update_types = ["message", "callback_query", "inline_query", "chosen_inline_result"]
        update_type = random.choice(update_types)
        
        if update_type == "message":
            self.client.post("/webhook", json={
                "update_id": random.randint(1, 1000000),
                "message": {
                    "message_id": random.randint(1, 1000000),
                    "from": {"id": random.randint(1, 100000), "is_bot": False, "first_name": "Test User"},
                    "chat": {"id": random.randint(1, 100000), "type": "private"},
                    "date": 1625097600,
                    "text": random.choice(["/start", "/menu", "/genre rock", "/song", "/artist", "/mood"])
                }
            })
        elif update_type == "callback_query":
            self.client.post("/webhook", json={
                "update_id": random.randint(1, 1000000),
                "callback_query": {
                    "id": str(random.randint(1, 1000000)),
                    "from": {"id": random.randint(1, 100000), "is_bot": False, "first_name": "Test User"},
                    "message": {
                        "message_id": random.randint(1, 1000000),
                        "chat": {"id": random.randint(1, 100000), "type": "private"},
                        "date": 1625097600,
                    },
                    "chat_instance": str(random.randint(1, 1000000)),
                    "data": random.choice(["menu", "mood_happy", "genre_rock", "50_song_123456"])
                }
            })
        elif update_type == "inline_query":
            self.client.post("/webhook", json={
                "update_id": random.randint(1, 1000000),
                "inline_query": {
                    "id": str(random.randint(1, 1000000)),
                    "from": {"id": random.randint(1, 100000), "is_bot": False, "first_name": "Test User"},
                    "query": random.choice(["son:Shape of You", "art:Ed Sheeran", "genre:rock"]),
                    "offset": ""
                }
            })
        elif update_type == "chosen_inline_result":
            self.client.post("/webhook", json={
                "update_id": random.randint(1, 1000000),
                "chosen_inline_result": {
                    "result_id": f"{random.choice(['track', 'artist', 'genre'])}_{random.randint(1, 1000000)}",
                    "from": {"id": random.randint(1, 100000), "is_bot": False, "first_name": "Test User"},
                    "query": random.choice(["son:Shape of You", "art:Ed Sheeran", "genre:rock"])
                }
            })
