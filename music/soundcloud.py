import requests

class SoundCloudDownloader:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.soundcloud.com"

    def get_track_info(self, track_url):
        """دریافت اطلاعات آهنگ از SoundCloud"""
        response = requests.get(f"{self.base_url}/resolve.json?url={track_url}&client_id={self.api_key}")
        return response.json()

    def download_track(self, track_id):
        """دانلود آهنگ از SoundCloud"""
        response = requests.get(f"{self.base_url}/tracks/{track_id}/stream?client_id={self.api_key}")
        return response.content