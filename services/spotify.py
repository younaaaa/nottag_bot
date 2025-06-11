import httpx # Using httpx
from config import Config

class SpotifyService:
    BASE_URL = "https://api.spotify.com/v1"

    @staticmethod
    def search(query: str, type: str = "track", limit: int = 10):
        if not Config.SPOTIFY_ACCESS_TOKEN:
            # In a real app, you'd have a mechanism to obtain/refresh this token.
            # For now, we assume it's a long-lived token from config.
            print("Error: SPOTIFY_ACCESS_TOKEN not configured.")
            return None # Or raise an error

        headers = {
            "Authorization": f"Bearer {Config.SPOTIFY_ACCESS_TOKEN}"
        }
        params = {
            "q": query,
            "type": type, # e.g., "track", "artist", "album"
            "limit": limit
        }
        try:
            with httpx.Client() as client:
                response = client.get(f"{SpotifyService.BASE_URL}/search", params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            # Spotify often returns detailed error messages in JSON
            error_details = e.response.json() if e.response.content else {}
            print(f"Spotify API HTTP error: {e.response.status_code} - {error_details.get('error', {}).get('message', e.response.text)}")
            if e.response.status_code == 401: # Unauthorized - token might be expired/invalid
                print("Spotify token might be invalid or expired.")
            return None
        except httpx.RequestError as e:
            print(f"Spotify API request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in SpotifyService.search: {e}")
            return None