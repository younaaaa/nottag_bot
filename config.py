import os
from dotenv import load_dotenv
from pathlib import Path
from cryptography.fernet import Fernet

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    LOG_DIR = BASE_DIR / 'logs'
    
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    FERNET = Fernet(ENCRYPTION_KEY.encode())
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMINS = list(map(int, os.getenv('ADMINS', '').split(','))) if os.getenv('ADMINS') else []
    
    DB_URL = os.getenv('DB_URL')
    MAX_RATE = int(os.getenv('MAX_REQUEST_RATE', 30))

    @staticmethod
    def encrypt(data: str) -> bytes:
        return Config.FERNET.encrypt(data.encode())

    @staticmethod
    def decrypt(encrypted: bytes) -> str:
        return Config.FERNET.decrypt(encrypted).decode()

for dir_path in [Config.DATA_DIR, Config.LOG_DIR]:
    dir_path.mkdir(exist_ok=True)