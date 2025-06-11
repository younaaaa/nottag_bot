import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services import AcoustIDService
from config import Config
import acoustid # For exception types

class TestAcoustIDService(unittest.TestCase):

    @patch.object(Config, 'ACOUSTID_API_KEY', 'testapikey')
    def test_01_initialization_success(self):
        print("\nRunning test: test_01_acoustid_initialization_success")
        try:
            service = AcoustIDService()
            self.assertIsNotNone(service)
            self.assertEqual(service.api_key, 'testapikey')
            print("Test test_01_acoustid_initialization_success PASSED")
        except Exception as e:
            self.fail(f"AcoustIDService initialization failed: {e}")


    @patch.object(Config, 'ACOUSTID_API_KEY', None)
    def test_02_initialization_fail_no_apikey(self):
        print("\nRunning test: test_02_acoustid_initialization_fail_no_apikey")
        with self.assertRaises(ValueError) as cm:
            AcoustIDService()
        self.assertIn("ACOUSTID_API_KEY not set", str(cm.exception))
        print("Test test_02_acoustid_initialization_fail_no_apikey PASSED")

    @patch('acoustid.fingerprint_file')
    @patch('acoustid.lookup')
    def test_03_lookup_fingerprint_success_mocked(self, mock_lookup, mock_fingerprint_file):
        print("\nRunning test: test_03_acoustid_lookup_success_mocked")
        mock_fingerprint_file.return_value = (180, 'dummy_fingerprint_encoded_string')
        mock_response = {
            'status': 'ok',
            'results': [{'score': 0.9, 'id': 'acoustid-result-id-123', 'recordings': [{'id': 'musicbrainz-id-456'}]}]
        }
        mock_lookup.return_value = mock_response

        # Create a temporary dummy file path for the test
        # No need to actually write to it as fingerprint_file is mocked
        temp_file_path = "temp_test_audio_for_acoustid.mp3"
        open(temp_file_path, 'a').close() # Just to have a file path

        with patch.object(Config, 'ACOUSTID_API_KEY', 'testapikey'):
            service = AcoustIDService()
            results = service.lookup_fingerprint(temp_file_path) # Use the temp path

        os.remove(temp_file_path) # Clean up the dummy file

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'acoustid-result-id-123')
        mock_fingerprint_file.assert_called_with(temp_file_path)
        mock_lookup.assert_called_with('testapikey', 'dummy_fingerprint_encoded_string', 180, meta=['recordings', 'releasegroups', 'compress'])
        print("Test test_03_acoustid_lookup_success_mocked PASSED")

    @patch('acoustid.fingerprint_file')
    def test_04_lookup_fingerprint_no_backend_mocked(self, mock_fingerprint_file):
        print("\nRunning test: test_04_acoustid_lookup_no_backend_mocked")
        mock_fingerprint_file.side_effect = acoustid.NoBackendError("fpcalc not found")

        with patch.object(Config, 'ACOUSTID_API_KEY', 'testapikey'):
            service = AcoustIDService()
            with self.assertRaises(RuntimeError) as cm:
                service.lookup_fingerprint("dummy.mp3")
            self.assertIn("FFmpeg/fpcalc", str(cm.exception)) # Check specific part of message
        print("Test test_04_acoustid_lookup_no_backend_mocked PASSED")

    @patch('acoustid.fingerprint_file')
    @patch('acoustid.lookup')
    def test_05_lookup_fingerprint_webservice_error_mocked(self, mock_lookup, mock_fingerprint_file):
        print("\nRunning test: test_05_acoustid_lookup_webservice_error_mocked")
        mock_fingerprint_file.return_value = (180, 'dummy_fingerprint_encoded_string')
        mock_lookup.side_effect = acoustid.WebServiceError("Service unavailable")

        with patch.object(Config, 'ACOUSTID_API_KEY', 'testapikey'):
            service = AcoustIDService()
            results = service.lookup_fingerprint("dummy.mp3")

        self.assertIsNone(results)
        print("Test test_05_acoustid_lookup_webservice_error_mocked PASSED (expected None)")

    @patch('acoustid.fingerprint_file')
    @patch('acoustid.lookup')
    def test_06_lookup_fingerprint_no_results_mocked(self, mock_lookup, mock_fingerprint_file):
        print("\nRunning test: test_06_acoustid_lookup_no_results_mocked")
        mock_fingerprint_file.return_value = (180, 'dummy_fingerprint_encoded_string')
        mock_lookup.return_value = {'status': 'ok', 'results': []} # Empty results list

        with patch.object(Config, 'ACOUSTID_API_KEY', 'testapikey'):
            service = AcoustIDService()
            results = service.lookup_fingerprint("dummy.mp3")

        self.assertIsNone(results) # Service's current logic returns None for empty 'results' list
        print("Test test_06_acoustid_lookup_no_results_mocked PASSED (expected None for empty results)")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
