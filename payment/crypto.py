import requests

class CryptoPayment:
    def __init__(self, api_url):
        self.api_url = api_url

    def create_payment(self, amount, currency, wallet_address):
        """ایجاد درخواست پرداخت با ارز دیجیتال"""
        payload = {
            "amount": amount,
            "currency": currency,
            "wallet_address": wallet_address
        }
        response = requests.post(f"{self.api_url}/create_payment", json=payload)
        return response.json()

    def verify_payment(self, transaction_id):
        """تأیید پرداخت با ارز دیجیتال"""
        response = requests.get(f"{self.api_url}/verify/{transaction_id}")
        return response.json()