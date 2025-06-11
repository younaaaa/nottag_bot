import musicbrainzngs
from config import Config # Assuming Config has MUSICBRAINZ_USERAGENT

class MusicBrainzService:
    def __init__(self):
        if not Config.MUSICBRAINZ_USERAGENT:
            raise ValueError("MUSICBRAINZ_USERAGENT not set in Config. Please set it in your .env file (e.g., YourAppName/1.0 (yourcontact@example.com))")

        # musicbrainzngs.set_useragent(app, version, contact=None)
        # Example: "MyAwesomeMusicBot", "1.0", "myemail@example.com"
        # We'll parse the MUSICBRAINZ_USERAGENT string if it's in "AppName/Version (contact)" format
        # or use it as is if it's just the app name.
        user_agent_parts = Config.MUSICBRAINZ_USERAGENT.split('/')
        app_name = user_agent_parts[0].strip()
        app_version = ""
        contact_email = None

        if len(user_agent_parts) > 1:
            version_contact_part = user_agent_parts[1].split('(')
            app_version = version_contact_part[0].strip()
            if len(version_contact_part) > 1:
                contact_email = version_contact_part[1].replace(')', '').strip()

        musicbrainzngs.set_useragent(
            app_name,
            app_version or "0.1", # Default version if not specified
            contact_email
        )

    def search_track(self, artist_name=None, track_title=None, album_title=None, limit=5):
        '''
        Searches for a track on MusicBrainz.
        Returns a list of results, with each result being a dictionary of relevant tag information.
        '''
        query_parts = {}
        if track_title:
            query_parts['recording'] = track_title
        if artist_name:
            query_parts['artist'] = artist_name
        if album_title:
            query_parts['release'] = album_title

        if not query_parts:
            return []

        try:
            # We are interested in recordings (tracks)
            # We can include release information to get album title, year, etc.
            # and artist-credit for artist name.
            result = musicbrainzngs.search_recordings(
                limit=limit,
                **query_parts
                # query=f"artist:{artist_name} recording:{track_title}" # Alternative query construction
            )
        except musicbrainzngs.WebServiceError as exc:
            print(f"MusicBrainz API Error: {exc}")
            return None # Indicate error
        except Exception as e:
            print(f"Unexpected error during MusicBrainz search: {e}")
            return None


        tracks_info = []
        if 'recording-list' in result:
            for recording in result['recording-list']:
                track_info = {'id': recording['id']}
                track_info['title'] = recording.get('title', 'N/A')

                if 'artist-credit' in recording and recording['artist-credit']:
                    track_info['artist'] = recording['artist-credit'][0]['artist']['name']

                if 'release-list' in recording and recording['release-list']:
                    release = recording['release-list'][0] # Take the first release
                    track_info['album'] = release.get('title', 'N/A')
                    if 'date' in release and release['date']:
                        track_info['year'] = release['date'].split('-')[0] # Extract year
                    # Potentially get track number from release's medium-list -> track-list
                    # This can be complex as a recording can appear on multiple releases with different track numbers.

                # Add other fields if available and relevant e.g. disambiguation
                tracks_info.append(track_info)
        return tracks_info

    def get_release_details(self, release_id):
        '''Gets detailed information for a specific release (album), including track list.'''
        try:
            # Includes: artists, labels, recordings (tracks), release-groups
            release = musicbrainzngs.get_release_by_id(release_id, includes=["recordings", "artist-credits"])
        except musicbrainzngs.WebServiceError as exc:
            print(f"MusicBrainz API Error getting release details: {exc}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

        if not release or 'release' not in release:
            return None

        release_data = release['release']
        album_info = {
            'id': release_data['id'],
            'title': release_data.get('title', 'N/A'),
            'date': release_data.get('date', '').split('-')[0] if release_data.get('date') else 'N/A',
            'artist': release_data['artist-credit'][0]['artist']['name'] if 'artist-credit' in release_data and release_data['artist-credit'] else 'N/A',
            'tracks': []
        }

        if 'medium-list' in release_data:
            for medium in release_data['medium-list']:
                if 'track-list' in medium:
                    for track in medium['track-list']:
                        track_details = {
                            'number': track.get('number'),
                            'title': track['recording'].get('title') if 'recording' in track else 'N/A',
                            'id': track['recording'].get('id') if 'recording' in track else None,
                            # 'length': track.get('length') # in milliseconds
                        }
                        album_info['tracks'].append(track_details)
        return album_info

# Example Usage (for testing, not part of the service file)
# if __name__ == '__main__':
#     # Make sure .env has MUSICBRAINZ_USERAGENT="YourBotName/1.0 (youremail@example.com)"
#     # from dotenv import load_dotenv
#     # load_dotenv() # To load .env for local testing
#
#     mb_service = MusicBrainzService()
#     # Test track search
#     results = mb_service.search_track(artist_name="Queen", track_title="Bohemian Rhapsody")
#     if results:
#         print("Search Results:")
#         for r in results:
#             print(f"  ID: {r.get('id')}, Title: {r.get('title')}, Artist: {r.get('artist')}, Album: {r.get('album')}, Year: {r.get('year')}")
#
#         # Test getting release details for the first album found (if any)
#         # This part is more complex as search_track results don't directly give release MBID easily for this purpose.
#         # A better test for get_release_details would be to find a known release_id.
#         # Example: Release ID for "News of the World" by Queen: 0234a2a6-e09c-3508-83e9-759837f03ef3
#         # release_info = mb_service.get_release_details("0234a2a6-e09c-3508-83e9-759837f03ef3")
#         # if release_info:
#         #    print("\nRelease Details:")
#         #    print(f"  Album: {release_info['title']}, Artist: {release_info['artist']}, Year: {release_info['date']}")
#         #    for track in release_info['tracks']:
#         #        print(f"    Track {track['number']}: {track['title']} (ID: {track['id']})")
#     else:
#         print("No results or error.")
