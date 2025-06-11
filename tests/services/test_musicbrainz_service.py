import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services import MusicBrainzService
from config import Config # To potentially modify config for testing
# Import musicbrainzngs specifically for its exception types if needed by mocks
import musicbrainzngs

class TestMusicBrainzService(unittest.TestCase):

    @patch.object(Config, 'MUSICBRAINZ_USERAGENT', 'TestApp/1.0 (test@example.com)')
    def test_01_initialization_success(self):
        print("\nRunning test: test_01_mb_initialization_success")
        try:
            # Patch set_useragent within the test to avoid actual calls if it's not already done globally for tests
            with patch('musicbrainzngs.set_useragent') as mock_set_ua:
                service = MusicBrainzService()
                self.assertIsNotNone(service)
                mock_set_ua.assert_called_with("TestApp", "1.0", "test@example.com")
            print("Test test_01_mb_initialization_success PASSED")
        except Exception as e:
            self.fail(f"MusicBrainzService initialization failed: {e}")

    @patch.object(Config, 'MUSICBRAINZ_USERAGENT', None)
    def test_02_initialization_fail_no_useragent(self):
        print("\nRunning test: test_02_mb_initialization_fail_no_useragent")
        with self.assertRaises(ValueError) as cm:
            MusicBrainzService()
        self.assertIn("MUSICBRAINZ_USERAGENT not set", str(cm.exception))
        print("Test test_02_mb_initialization_fail_no_useragent PASSED (expected ValueError)")

    @patch('musicbrainzngs.set_useragent')
    @patch('musicbrainzngs.search_recordings')
    def test_03_search_track_success_mocked(self, mock_search_recordings, mock_set_useragent_call):
        # mock_set_useragent_call is for the set_useragent call inside MusicBrainzService.__init__
        print("\nRunning test: test_03_mb_search_track_success_mocked")
        mock_response = {
            'recording-list': [{
                'id': 'some-mbid',
                'title': 'Test Song',
                'artist-credit': [{'artist': {'name': 'Test Artist'}}],
                'release-list': [{'title': 'Test Album', 'date': '2023-01-01'}]
            }]
        }
        mock_search_recordings.return_value = mock_response

        with patch.object(Config, 'MUSICBRAINZ_USERAGENT', 'TestApp/1.0 (test@example.com)'):
            service = MusicBrainzService() # Will call the mocked set_useragent
            results = service.search_track(artist_name="Test Artist", track_title="Test Song")

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Song')
        self.assertEqual(results[0]['artist'], 'Test Artist')
        self.assertEqual(results[0]['album'], 'Test Album')
        self.assertEqual(results[0]['year'], '2023')
        mock_set_useragent_call.assert_called()
        mock_search_recordings.assert_called_once_with(limit=5, artist='Test Artist', recording='Test Song')
        print("Test test_03_mb_search_track_success_mocked PASSED")

    @patch('musicbrainzngs.set_useragent')
    @patch('musicbrainzngs.search_recordings')
    def test_04_search_track_api_error_mocked(self, mock_search_recordings, mock_set_useragent_call):
        print("\nRunning test: test_04_mb_search_track_api_error_mocked")
        mock_search_recordings.side_effect = musicbrainzngs.WebServiceError("API unavailable")

        with patch.object(Config, 'MUSICBRAINZ_USERAGENT', 'TestApp/1.0 (test@example.com)'):
            service = MusicBrainzService()
            results = service.search_track(artist_name="Test Artist", track_title="Test Song")

        self.assertIsNone(results)
        print("Test test_04_mb_search_track_api_error_mocked PASSED (expected None)")

    @patch('musicbrainzngs.set_useragent')
    @patch('musicbrainzngs.get_release_by_id')
    def test_05_get_release_details_success_mocked(self, mock_get_release_by_id, mock_set_useragent_call):
        print("\nRunning test: test_05_mb_get_release_details_success_mocked")
        mock_response = {
            'release': {
                'id': 'release-id-123',
                'title': 'Test Album Detailed',
                'date': '2022-03-03',
                'artist-credit': [{'artist': {'name': 'Detailed Artist'}}],
                'medium-list': [{
                    'track-list': [{
                        'number': '1',
                        'recording': {'title': 'Track 1', 'id': 'track-id-1'}
                    }]
                }]
            }
        }
        mock_get_release_by_id.return_value = mock_response
        with patch.object(Config, 'MUSICBRAINZ_USERAGENT', 'TestApp/1.0 (test@example.com)'):
            service = MusicBrainzService()
            details = service.get_release_details('release-id-123')

        self.assertIsNotNone(details)
        self.assertEqual(details['title'], 'Test Album Detailed')
        self.assertEqual(details['artist'], 'Detailed Artist')
        self.assertEqual(details['date'], '2022')
        self.assertEqual(len(details['tracks']), 1)
        self.assertEqual(details['tracks'][0]['title'], 'Track 1')
        mock_get_release_by_id.assert_called_once_with('release-id-123', includes=["recordings", "artist-credits"])
        print("Test test_05_mb_get_release_details_success_mocked PASSED")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
