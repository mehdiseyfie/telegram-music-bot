import unittest
import time
from unittest.mock import patch, MagicMock
from spotify_service.spotify.cache import (
    cached_search_track,
    cached_get_artist,
    cached_get_recommendations,
    cached_spotify_search
)

class TestSpotifyCache(unittest.TestCase):
    def setUp(self):
        # Reset all caches before each test
        cached_search_track.cache_clear()
        cached_get_artist.cache_clear()
        cached_get_recommendations.cache_clear()
        cached_spotify_search.cache_clear()

    @patch('spotify_service.spotify.api.search_track')
    def test_cached_search_track(self, mock_search_track):
        mock_search_track.return_value = [{'name': 'Test Track'}]

        # First call
        result1 = cached_search_track("test")
        # Second call
        result2 = cached_search_track("test")

        mock_search_track.assert_called_once()
        self.assertEqual(result1, result2)

    @patch('spotify_service.spotify.api.get_artist')
    def test_cached_get_artist(self, mock_get_artist):
        mock_get_artist.return_value = {'name': 'Test Artist'}

        # First call
        result1 = cached_get_artist("artist_id")
        # Second call
        result2 = cached_get_artist("artist_id")

        mock_get_artist.assert_called_once()
        self.assertEqual(result1, result2)

    @patch('spotify_service.spotify.api.get_recommendations')
    def test_cached_get_recommendations(self, mock_get_recommendations):
        mock_get_recommendations.return_value = [{'name': 'Recommended Track'}]

        # First call
        result1 = cached_get_recommendations("track1,track2", 10)
        # Second call
        result2 = cached_get_recommendations("track1,track2", 10)

        mock_get_recommendations.assert_called_once()
        self.assertEqual(result1, result2)

    @patch('spotify_service.spotify.api.spotify_search')
    def test_cached_spotify_search(self, mock_spotify_search):
        mock_spotify_search.return_value = {'tracks': {'items': []}}

        # First call
        result1 = cached_spotify_search("test", 'track', 10)
        # Second call
        result2 = cached_spotify_search("test", 'track', 10)

        mock_spotify_search.assert_called_once()
        self.assertEqual(result1, result2)

    def test_different_parameters(self):
        with patch('spotify_service.spotify.api.spotify_search') as mock_spotify_search:
            mock_spotify_search.return_value = {'tracks': {'items': []}}

            cached_spotify_search("test1", 'track', 10)
            cached_spotify_search("test2", 'track', 10)
            cached_spotify_search("test1", 'artist', 10)
            cached_spotify_search("test1", 'track', 20)

            self.assertEqual(mock_spotify_search.call_count, 4)

    def test_cache_expiration(self):
        with patch('spotify_service.spotify.api.spotify_search') as mock_spotify_search:
            mock_spotify_search.return_value = {'tracks': {'items': []}}

            # Override the cache decorator to expire after 1 second
            def quick_expiry_cache(**kwargs):
                return timed_lru_cache(seconds=0.1)

            with patch('spotify_service.spotify.cache.timed_lru_cache', quick_expiry_cache):
                # First call
                cached_spotify_search("test", 'track', 10)
                
                # Wait for cache to expire
                time.sleep(0.2)
                
                # Second call
                cached_spotify_search("test", 'track', 10)

                self.assertEqual(mock_spotify_search.call_count, 1)

def test_cache_performance():
    print("\nTesting cache performance:")
    
    # Test cached_search_track
    print("\nTesting cached_search_track:")
    start = time.time()
    result1 = cached_search_track("test track")
    time1 = time.time() - start

    start = time.time()
    result2 = cached_search_track("test track")
    time2 = time.time() - start

    print(f"First call: {time1:.4f} seconds")
    print(f"Second call: {time2:.4f} seconds")
    print(f"Cache hit: {time2 < time1}")

    # Test cached_get_artist
    print("\nTesting cached_get_artist:")
    start = time.time()
    result1 = cached_get_artist("test_artist_id")
    time1 = time.time() - start

    start = time.time()
    result2 = cached_get_artist("test_artist_id")
    time2 = time.time() - start

    print(f"First call: {time1:.4f} seconds")
    print(f"Second call: {time2:.4f} seconds")
    print(f"Cache hit: {time2 < time1}")

    # Test cached_get_recommendations
    print("\nTesting cached_get_recommendations:")
    start = time.time()
    result1 = cached_get_recommendations("track1,track2", 10)
    time1 = time.time() - start

    start = time.time()
    result2 = cached_get_recommendations("track1,track2", 10)
    time2 = time.time() - start

    print(f"First call: {time1:.4f} seconds")
    print(f"Second call: {time2:.4f} seconds")
    print(f"Cache hit: {time2 < time1}")

    # Test cached_spotify_search
    print("\nTesting cached_spotify_search:")
    for search_type in ['track', 'artist', 'playlist']:
        print(f"\nTesting {search_type} search:")
        start = time.time()
        result1 = cached_spotify_search(f"test {search_type}", search_type, 10)
        time1 = time.time() - start

        start = time.time()
        result2 = cached_spotify_search(f"test {search_type}", search_type, 10)
        time2 = time.time() - start

        print(f"First call: {time1:.4f} seconds")
        print(f"Second call: {time2:.4f} seconds")
        print(f"Cache hit: {time2 < time1}")

if __name__ == '__main__':
    unittest.main()