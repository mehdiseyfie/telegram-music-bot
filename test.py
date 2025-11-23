import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from telegram import Update
from telegram.ext import CallbackContext
from bot_service.bot.handlers.start import start_command, show_main_menu
from bot_service.bot.handlers.search import inline_search
from spotify_service.spotify.api import search_track, get_artist, get_recommendations
from database_service.database.crud import get_user, create_user, get_playlist
from bot_service.bot.services.spotify import create_playlist as bot_create_playlist
import pytest
from unittest.mock import AsyncMock, patch
from api_gateway.gateway.main import app

class TestBotService(unittest.TestCase):
    def setUp(self):
        self.update = Mock(spec=Update)
        self.context = Mock(spec=CallbackContext)

    def test_start_command(self):
        self.update.effective_user = Mock(first_name="Test")
        self.update.message = Mock()
        start_command(self.update, self.context)
        self.update.message.reply_text.assert_called_once()

    def test_show_main_menu(self):
        self.update.message = Mock()
        show_main_menu(self.update, self.context)
        self.update.message.reply_text.assert_called_once()

    @patch('bot_service.bot.handlers.search.sp')
    def test_inline_search(self, mock_sp):
        mock_sp.search.return_value = {'tracks': {'items': []}}
        self.update.inline_query = Mock(query="test")
        inline_search(self.update, self.context)
        self.update.inline_query.answer.assert_called_once()

class TestSpotifyService(unittest.TestCase):
    @patch('spotify_service.spotify.api.sp')
    def test_search_track(self, mock_sp):
        mock_sp.search.return_value = {'tracks': {'items': []}}
        result = search_track("test")
        self.assertEqual(result, [])

    @patch('spotify_service.spotify.api.sp')
    def test_get_artist(self, mock_sp):
        mock_sp.artist.return_value = {'name': 'Test Artist'}
        result = get_artist("test_id")
        self.assertEqual(result['name'], 'Test Artist')

    @patch('spotify_service.spotify.api.sp')
    def test_get_recommendations(self, mock_sp):
        mock_sp.recommendations.return_value = {'tracks': []}
        result = get_recommendations(["test_id"])
        self.assertEqual(result, {'tracks': []})

class TestDatabaseService(unittest.TestCase):
    def setUp(self):
        self.session = Mock()

    def test_get_user(self):
        self.session.query().filter().first.return_value = Mock(telegram_id=123)
        user = get_user(self.session, 123)
        self.assertEqual(user.telegram_id, 123)

    def test_create_user(self):
        user = create_user(self.session, 123, "test_user")
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

    def test_get_playlist(self):
        self.session.query().filter().first.return_value = Mock(spotify_id="test_id")
        playlist = get_playlist(self.session, "test_id")
        self.assertEqual(playlist.spotify_id, "test_id")

    @patch('bot_service.bot.services.spotify.sp')
    def test_create_playlist(self, mock_sp):
        mock_sp.user_playlist_create.return_value = {'id': 'test_id', 'external_urls': {'spotify': 'https://open.spotify.com/playlist/test_id'}}
        mock_sp.playlist_add_items.return_value = None
        result = bot_create_playlist("Test Playlist", ["track1", "track2"])
        self.assertEqual(result, 'https://open.spotify.com/playlist/test_id')

@pytest.fixture
def client():
    return TestClient(app)

class TestApiGateway:
    @pytest.mark.asyncio
    @patch('api_gateway.gateway.main.httpx.AsyncClient.post')
    async def test_search_track(self, mock_post, client):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'tracks': []}
        mock_post.return_value = mock_response

        response = client.post("/search_track", json={"query": "test"})

        assert response.status_code == 200
        assert response.json() == {'tracks': []}
        mock_post.assert_called_once_with("http://spotify_service:8000/search_track", json={"query": "test"})

    @pytest.mark.asyncio
    @patch('api_gateway.gateway.main.httpx.AsyncClient.post')
    async def test_create_playlist(self, mock_post, client):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'playlist_id'}
        mock_post.return_value = mock_response

        response = client.post("/create_playlist", json={"name": "Test Playlist", "tracks": ["track1", "track2"], "user_id": 123})

        assert response.status_code == 200
        assert response.json() == {'id': 'playlist_id'}
        mock_post.assert_called_once_with("http://database_service:8000/create_playlist", json={"name": "Test Playlist", "tracks": ["track1", "track2"], "user_id": 123})

    @pytest.mark.asyncio
    @patch('api_gateway.gateway.main.httpx.AsyncClient.post')
    async def test_search_track_error(self, mock_post, client):
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'detail': 'Spotify service error'}
        mock_post.return_value = mock_response

        response = client.post("/search_track", json={"query": "test"})

        assert response.status_code == 500
        assert response.json() == {'detail': 'Spotify service error'}

    @pytest.mark.asyncio
    @patch('api_gateway.gateway.main.httpx.AsyncClient.post')
    async def test_create_playlist_error(self, mock_post, client):
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'detail': 'Database service error'}
        mock_post.return_value = mock_response

        response = client.post("/create_playlist", json={"name": "Test Playlist", "tracks": ["track1", "track2"], "user_id": 123})

        assert response.status_code == 500
        assert response.json() == {'detail': 'Database service error'}

if __name__ == '__main__':
    unittest.main()