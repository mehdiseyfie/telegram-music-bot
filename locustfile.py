import random
import time
from locust import HttpUser, task, between


LANGUAGES = ['en', 'fa']
SONGS = ["Shape of You", "Despacito", "Blinding Lights"]
ARTISTS = ["Ed Sheeran", "Taylor Swift", "Drake"]
MOODS = ["Happy", "Sad", "Energetic", "Calm"]


class TelegramBotUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:8000"

    def on_start(self):
        self.user_id = random.randint(1, 1000000)
        self.first_name = f"User{self.user_id}"
        self.language = random.choice(LANGUAGES)

    @task(5)
    def start_command(self):
        self.client.post("/bot", json={
            "update_id": random.randint(1, 1000000),
            "message": {
                "message_id": random.randint(1, 1000000),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": self.first_name,
                    "language_code": self.language
                },
                "chat": {
                    "id": self.user_id,
                    "first_name": self.first_name,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        })

    @task(10)
    def search_song(self):
        query = random.choice(SONGS)
        self.client.post("/bot", json={
            "update_id": random.randint(1, 1000000),
            "inline_query": {
                "id": str(random.randint(1, 1000000)),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": self.first_name,
                    "language_code": self.language
                },
                "query": f"son:{query}",
                "offset": ""
            }
        })

    @task(8)
    def search_artist(self):
        query = random.choice(ARTISTS)
        self.client.post("/bot", json={
            "update_id": random.randint(1, 1000000),
            "inline_query": {
                "id": str(random.randint(1, 1000000)),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": self.first_name,
                    "language_code": self.language
                },
                "query": f"art:{query}",
                "offset": ""
            }
        })

    @task(6)
    def create_playlist(self):
        mood = random.choice(["Happy", "Sad", "Energetic", "Calm"])
        self.client.post("/bot", json={
            "update_id": random.randint(1, 1000000),
            "callback_query": {
                "id": str(random.randint(1, 1000000)),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": self.first_name,
                    "language_code": self.language
                },
                "message": {
                    "message_id": random.randint(1, 1000000),
                    "chat": {
                        "id": self.user_id,
                        "first_name": self.first_name,
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Select a mood"
                },
                "chat_instance": str(random.randint(1, 1000000)),
                "data": f"mood_{mood}"
            }
        })

    @task(4)
    def change_language(self):
        new_language = random.choice(LANGUAGES)
        self.client.post("/bot", json={
            "update_id": random.randint(1, 1000000),
            "callback_query": {
                "id": str(random.randint(1, 1000000)),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": self.first_name,
                    "language_code": self.language
                },
                "message": {
                    "message_id": random.randint(1, 1000000),
                    "chat": {
                        "id": self.user_id,
                        "first_name": self.first_name,
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Select a language"
                },
                "chat_instance": str(random.randint(1, 1000000)),
                "data": f"lang_{new_language}"
            }
        })

    @task(3)
    def explore_genres(self):
        self.client.post("/bot", json={
            "update_id": random.randint(1, 1000000),
            "callback_query": {
                "id": str(random.randint(1, 1000000)),
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": self.first_name,
                    "language_code": self.language
                },
                "message": {
                    "message_id": random.randint(1, 1000000),
                    "chat": {
                        "id": self.user_id,
                        "first_name": self.first_name,
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "Explore genres"
                },
                "chat_instance": str(random.randint(1, 1000000)),
                "data": "genre"
            }
        })