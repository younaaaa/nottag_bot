import requests
from config import Config
import httpx # Using httpx as it's in requirements and good for async later

# It's better to use a shared httpx.AsyncClient instance if making many calls in an async app,
# but for a simple service method, a temporary client is okay.
# For now, let's make this a synchronous method using httpx.Client for consistency.

class SoundCloudService:
    BASE_URL = "https://api.soundcloud.com"
    
    @staticmethod
    def search(query: str, limit: int = 10):
        if not Config.SOUNDCLOUD_CLIENT_ID:
            print("Error: SOUNDCLOUD_CLIENT_ID not configured.")
            return None # Or raise an error

        params = {
            "q": query,
            "client_id": Config.SOUNDCLOUD_CLIENT_ID,
            "limit": limit,
            "linked_partitioning": 1 # For pagination if needed in future
        }
        try:
            # Using httpx synchronously for now
            with httpx.Client() as client:
                response = client.get(f"{SoundCloudService.BASE_URL}/tracks", params=params)
                response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"SoundCloud API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"SoundCloud API request error: {e}")
            return None
        except Exception as e: # Catch other potential errors like JSONDecodeError implicitly by httpx or other issues
            print(f"Unexpected error in SoundCloudService.search: {e}")
            return None