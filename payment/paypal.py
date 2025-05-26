import requests

class PayPal:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.paypal.com/v1"

    def create_payment(self, amount, currency, return_url, cancel_url):
        payload = {
            "intent": "sale",
            "transactions": [{"amount": {"total": amount, "currency": currency}}],
            "redirect_urls": {"return_url": return_url, "cancel_url": cancel_url}
        }
        response = requests.post(f"{self.base_url}/payments/payment", json=payload)
        return response.json()