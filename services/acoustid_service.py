import acoustid
from config import Config # Assuming Config has ACOUSTID_API_KEY

class AcoustIDService:
    def __init__(self):
        if not Config.ACOUSTID_API_KEY:
            raise ValueError("ACOUSTID_API_KEY not set in Config. Please set it in your .env file.")
        self.api_key = Config.ACOUSTID_API_KEY

    def lookup_fingerprint(self, file_path, desired_metadata=['recordings', 'releasegroups', 'compress']):
        '''
        Generates a fingerprint for the given audio file and looks it up on AcoustID.

        :param file_path: Path to the audio file.
        :param desired_metadata: A list of metadata parts to fetch from AcoustID.
                                 Common options: 'recordings', 'recordingids', 'releases',
                                 'releasegroups', 'tracks', 'compress', 'usermeta', 'sources'.
        :return: A list of results from AcoustID, or None if an error occurs or no match.
                 Each result typically contains a 'score' and a list of 'recordings'
                 (which include MusicBrainz IDs).
        '''
        try:
            # Fingerprint the file (duration, fingerprint_encoded)
            duration, fp_encoded = acoustid.fingerprint_file(file_path)

            # Submit the fingerprint to AcoustID API
            # The 'meta' parameter specifies what information to return.
            # 'recordings' includes a list of recordings, each with MBIDs.
            # 'releasegroups' includes album information.
            results = acoustid.lookup(self.api_key, fp_encoded, duration, meta=desired_metadata)

            # results is a dictionary structure, often with a 'results' list
            # e.g. {'status': 'ok', 'results': [{...}]}
            if results and results.get('status') == 'ok' and results.get('results'):
                return results.get('results')
            else:
                # Log or handle cases where status is not 'ok' or no results list
                print(f"AcoustID lookup for {file_path} did not return 'ok' status or results: {results.get('status')}")
                return None

        except acoustid.NoBackendError:
            # This error occurs if FFmpeg (or another backend like fpcalc) is not found.
            # The bot needs FFmpeg installed on the server.
            print("Error: AcoustID backend (e.g., FFmpeg/fpcalc) not found. Please ensure it's installed and in PATH.")
            # You might want to raise a specific exception or return a distinct error code/message.
            raise RuntimeError("AcoustID backend (e.g., FFmpeg/fpcalc) not found.")
        except acoustid.WebServiceError as exc:
            print(f"AcoustID WebServiceError: {exc}")
            return None # Indicate API communication error
        except Exception as e:
            print(f"An unexpected error occurred during AcoustID lookup for {file_path}: {e}")
            return None

# Example Usage (for testing, not part of the service file)
# if __name__ == '__main__':
#     # Make sure .env has ACOUSTID_API_KEY
#     # import os # Required for os.path.exists in example
#     # from dotenv import load_dotenv
#     # load_dotenv() # To load .env for local testing
#
#     # You'll need an actual audio file for testing.
#     # test_audio_file = "path/to/your/test_audio.mp3"
#     # if not os.path.exists(test_audio_file):
#     #     print(f"Test audio file not found: {test_audio_file}")
#     # else:
#     #     acoustid_service = AcoustIDService()
#     #     acoustid_results = acoustid_service.lookup_fingerprint(test_audio_file)
#     #
#     #     if acoustid_results:
#     #         print("AcoustID Results:")
#     #         for result in acoustid_results:
#     #             score = result.get('score')
#     #             print(f"  Score: {score*100:.2f}%")
#     #             if 'recordings' in result:
#     #                 for recording in result['recordings']:
#     #                     mbid = recording.get('id')
#     #                     title = recording.get('title', 'N/A') # May not be available directly here
#     #                     artist_list = []
#     #                     if 'artists' in recording:
#     #                         for artist_info in recording['artists']:
#     #                             artist_list.append(artist_info.get('name', 'Unknown Artist'))
#     #                     artists_str = ", ".join(artist_list)
#     #                     print(f"    MBID: {mbid}, Title (approx): {title}, Artists: {artists_str}")
#     #     elif acoustid_results is None: # Explicit None means error
#     #         print("An error occurred with AcoustID lookup.")
#     #     else: # Empty list or other non-None falsy value means no match
#     #         print("No match found on AcoustID.")
