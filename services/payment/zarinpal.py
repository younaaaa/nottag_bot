import requests
from config import Config

class ZarinpalPayment:
    BASE_URL = "https://api.zarinpal.com/pg/v4/payment"
    
    @staticmethod
    def create_payment(amount, description):
        payload = {
            "merchant_id": Config.ZARINPAL_MERCHANT_ID,
            "amount": amount,
            "callback_url": Config.ZARINPAL_CALLBACK_URL,
            "description": description
        }
        
        response = requests.post(f"{BASE_URL}/request.json", json=payload)
        return response.json()