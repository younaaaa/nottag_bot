import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # مثلا: https://your-app-name.onrender.com
    PORT = int(os.getenv('PORT', 10000))  # پورت اجباری در Render

    # Database
    DB_URL = os.getenv('DB_URL')

    # External APIs
    SOUNDCLOUD_CLIENT_ID = os.getenv('SOUNDCLOUD_CLIENT_ID')
    SPOTIFY_ACCESS_TOKEN = os.getenv('SPOTIFY_ACCESS_TOKEN')
    MUSICBRAINZ_USERAGENT = os.getenv('MUSICBRAINZ_USERAGENT')
    ACOUSTID_API_KEY = os.getenv('ACOUSTID_API_KEY')
    GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')

    # Redis
    REDIS_URL = os.getenv('REDIS_URL')
