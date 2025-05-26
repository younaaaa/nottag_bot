import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    PAYMENT_GATEWAYS = ["ZarinPal", "PayPal", "Crypto"]
    DEFAULT_LANGUAGE = "fa"