import requests
from config import Config

class SoundCloudService:
    BASE_URL = "https://api.soundcloud.com"
    
    @staticmethod
    def search(query):
        params = {
            "q": query,
            "client_id": Config.SOUNDCLOUD_CLIENT_ID
        }
        response = requests.get(f"{BASE_URL}/tracks", params=params)
        return response.json()