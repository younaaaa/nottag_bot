import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # مثلا: https://your-app-name.onrender.com
    PORT = int(os.getenv('PORT', 10000))  # پورت اجباری در Render