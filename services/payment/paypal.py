import requests
from config import Config

class PayPalPayment:
    BASE_URL = "https://api.paypal.com/v1"
    
    @staticmethod
    def create_payment(amount, currency):
        headers = {
            "Authorization": f"Bearer {Config.PAYPAL_SECRET}"
        }
        payload = {
            "amount": amount,
            "currency": currency
        }
        
        response = requests.post(f"{BASE_URL}/payments", json=payload, headers=headers)
        return response.json()