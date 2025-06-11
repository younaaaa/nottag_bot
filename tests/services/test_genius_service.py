import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services import GeniusService
from config import Config
# lyricsgenius might be needed for its specific exception or Song object
# For mocking Song, we can use MagicMock with a spec if available, or just MagicMock
# from lyricsgenius.song import Song # If needed for spec

class TestGeniusService(unittest.TestCase):

    @patch.object(Config, 'GENIUS_ACCESS_TOKEN', 'testaccesstoken')
    @patch('lyricsgenius.Genius') # Mock the external library
    def test_01_initialization_success(self, MockGeniusAPIConstructor):
        print("\nRunning test: test_01_genius_initialization_success")
        # We patch the Genius constructor itself to prevent any actual API calls or setup it might do.
        # The instance of the service will then hold a mock object for self.genius_api
        service = GeniusService()
        self.assertIsNotNone(service)
        MockGeniusAPIConstructor.assert_called_with(
            'testaccesstoken',
            verbose=False,
            remove_section_headers=True,
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)"]
        )
        print("Test test_01_genius_initialization_success PASSED")

    @patch.object(Config, 'GENIUS_ACCESS_TOKEN', None)
    def test_02_initialization_fail_no_token(self):
        print("\nRunning test: test_02_genius_initialization_fail_no_token")
        with self.assertRaises(ValueError) as cm:
            GeniusService()
        self.assertIn("GENIUS_ACCESS_TOKEN not set", str(cm.exception))
        print("Test test_02_genius_initialization_fail_no_token PASSED")

    @patch('lyricsgenius.Genius')
    def test_03_search_lyrics_success_mocked(self, MockGeniusAPIConstructor):
        print("\nRunning test: test_03_genius_search_lyrics_success_mocked")
        mock_api_instance = MockGeniusAPIConstructor.return_value

        # Mocking the Song object that search_song is expected to return
        mock_song = MagicMock()
        mock_song.lyrics = "Test lyrics line 1\nTest lyrics line 2"
        mock_api_instance.search_song.return_value = mock_song

        with patch.object(Config, 'GENIUS_ACCESS_TOKEN', 'testaccesstoken'):
            service = GeniusService() # This will use the mocked Genius API
            lyrics = service.search_lyrics("Test Title", "Test Artist")

        self.assertIsNotNone(lyrics)
        # The cleaning logic in GeniusService might alter this slightly.
        # For this test, assume simple case or adjust expected if cleaning is aggressive.
        # Current cleaning: removes "EmbedShare..." (not present), removes title line if it matches.
        # Let's assume for "Test Title Lyrics" it would be removed.
        # If the first line was just "Test Title", it might not be removed by current logic.
        # The lyrics cleaning in the service is:
        # if len(lines) > 1 and lines[0].strip().lower().startswith(title.lower()):
        #    if "lyrics" in lines[0].lower() or artist.lower() in lines[0].lower():
        #       lyrics_text = "\n".join(lines[1:]).strip()
        # So, "Test Title Lyrics" would become empty if it's the only line after header.
        # If mock_song.lyrics = "Test Title Lyrics\nLine 2", then "Line 2" would be expected.
        # Let's use lyrics that won't trigger the header removal for simplicity of this test.
        expected_lyrics = "Test lyrics line 1\nTest lyrics line 2" # Assuming no header was matched by cleaning
        self.assertEqual(lyrics, expected_lyrics)
        mock_api_instance.search_song.assert_called_with("Test Title", "Test Artist")
        print("Test test_03_genius_search_lyrics_success_mocked PASSED")

    @patch('lyricsgenius.Genius')
    def test_04_search_lyrics_not_found_mocked(self, MockGeniusAPIConstructor):
        print("\nRunning test: test_04_genius_search_lyrics_not_found_mocked")
        mock_api_instance = MockGeniusAPIConstructor.return_value
        mock_api_instance.search_song.return_value = None

        with patch.object(Config, 'GENIUS_ACCESS_TOKEN', 'testaccesstoken'):
            service = GeniusService()
            lyrics = service.search_lyrics("Unknown Title", "Unknown Artist")

        self.assertIsNone(lyrics)
        print("Test test_04_genius_search_lyrics_not_found_mocked PASSED")

    @patch('lyricsgenius.Genius')
    def test_05_search_lyrics_api_exception_mocked(self, MockGeniusAPIConstructor):
        print("\nRunning test: test_05_genius_search_lyrics_api_exception_mocked")
        mock_api_instance = MockGeniusAPIConstructor.return_value
        mock_api_instance.search_song.side_effect = Exception("API unavailable")

        with patch.object(Config, 'GENIUS_ACCESS_TOKEN', 'testaccesstoken'):
            service = GeniusService()
            lyrics = service.search_lyrics("Test Title", "Test Artist")

        self.assertIsNone(lyrics)
        print("Test test_05_genius_search_lyrics_api_exception_mocked PASSED")

    @patch('lyricsgenius.Genius')
    def test_06_search_lyrics_cleaning_removes_header(self, MockGeniusAPIConstructor):
        print("\nRunning test: test_06_genius_search_lyrics_cleaning_removes_header")
        mock_api_instance = MockGeniusAPIConstructor.return_value
        mock_song = MagicMock()
        # Simulate lyrics that include a typical Genius header
        mock_song.lyrics = "Test Title Lyrics\nReal first line\nSecond line"
        mock_api_instance.search_song.return_value = mock_song

        with patch.object(Config, 'GENIUS_ACCESS_TOKEN', 'testaccesstoken'):
            service = GeniusService()
            lyrics = service.search_lyrics("Test Title", "Test Artist") # Title and artist match the header

        expected_cleaned_lyrics = "Real first line\nSecond line"
        self.assertEqual(lyrics, expected_cleaned_lyrics)
        print("Test test_06_genius_search_lyrics_cleaning_removes_header PASSED")

    @patch('lyricsgenius.Genius')
    def test_07_search_lyrics_cleaning_removes_footer(self, MockGeniusAPIConstructor):
        print("\nRunning test: test_07_genius_search_lyrics_cleaning_removes_footer")
        mock_api_instance = MockGeniusAPIConstructor.return_value
        mock_song = MagicMock()
        mock_song.lyrics = "Meaningful lyrics\nYou might also like\nSome other junk\n123Embed"
        mock_api_instance.search_song.return_value = mock_song

        with patch.object(Config, 'GENIUS_ACCESS_TOKEN', 'testaccesstoken'):
            service = GeniusService()
            lyrics = service.search_lyrics("Test Song", "Artist")

        expected_cleaned_lyrics = "Meaningful lyrics" # "You might also like" and subsequent lines should be gone
        self.assertEqual(lyrics, expected_cleaned_lyrics)
        print("Test test_07_genius_search_lyrics_cleaning_removes_footer PASSED")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
