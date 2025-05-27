import os
from zarinpal import ZarinPal

def create_payment(amount: int, description: str, callback_url: str) -> dict:
    merchant_id = os.getenv("ZARINPAL_MERCHANT_ID")
    zarinpal = ZarinPal(merchant_id)
    return zarinpal.create_payment(amount, description, callback_url)
