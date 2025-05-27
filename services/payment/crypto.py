import requests
from config import Config

class CryptoPayment:
    BASE_URL = "https://api.nowpayments.io/v1"
    
    @staticmethod
    def create_payment(amount, currency):
        headers = {
            "x-api-key": Config.CRYPTO_API_KEY
        }
        payload = {
            "price_amount": amount,
            "price_currency": "usd",
            "pay_currency": currency
        }
        
        response = requests.post(f"{BASE_URL}/payment", json=payload, headers=headers)
        return response.json()