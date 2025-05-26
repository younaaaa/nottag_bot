from langdetect import detect

def detect_user_language(text):
    """تشخیص زبان کاربر بر اساس متن ورودی"""
    return detect(text)