from .zarinpal import ZarinpalPayment
from .paypal import PayPalPayment
from .crypto import CryptoPayment

class PaymentService:
    @staticmethod
    def get_gateway(country):
        if country == 'IR':
            return ZarinpalPayment()
        else:
            return PayPalPayment()