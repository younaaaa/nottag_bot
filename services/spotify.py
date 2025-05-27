import requests
from config import Config

class SpotifyService:
    BASE_URL = "https://api.spotify.com/v1"
    
    @staticmethod
    def search(query):
        headers = {
            "Authorization": f"Bearer {Config.SPOTIFY_ACCESS_TOKEN}"
        }
        params = {
            "q": query,
            "type": "track"
        }
        response = requests.get(f"{BASE_URL}/search", params=params, headers=headers)
        return response.json()