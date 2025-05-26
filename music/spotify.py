import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyManager:
    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id, client_secret))

    def get_track_info(self, track_url):
        """دریافت اطلاعات آهنگ از Spotify"""
        track = self.sp.track(track_url)
        return {
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"]
        }