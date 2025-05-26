import hashlib

def generate_hash(value):
    """تولید هش SHA256 برای داده‌های حساس"""
    return hashlib.sha256(value.encode()).hexdigest()

def validate_payment_signature(data, secret_key):
    """اعتبارسنجی امضای دیجیتال پرداخت"""
    expected_signature = generate_hash(data + secret_key)
    return expected_signature == data.get("signature")