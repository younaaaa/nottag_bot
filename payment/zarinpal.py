import requests

class ZarinPal:
    def __init__(self, merchant_id):
        self.merchant_id = merchant_id
        self.base_url = "https://www.zarinpal.com/pg/rest/WebGate"

    def create_payment(self, amount, description, callback_url):
        payload = {
            "MerchantID": self.merchant_id,
            "Amount": amount,
            "Description": description,
            "CallbackURL": callback_url
        }
        response = requests.post(f"{self.base_url}/PaymentRequest.json", json=payload)
        return response.json()