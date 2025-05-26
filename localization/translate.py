import json

class Translator:
    def __init__(self, lang="fa"):
        self.lang = lang
        self.load_translation()

    def load_translation(self):
        """بارگذاری فایل ترجمه بر اساس زبان انتخابی"""
        with open(f"locales/{self.lang}/messages.json", "r", encoding="utf-8") as file:
            self.messages = json.load(file)

    def translate(self, key):
        """دریافت متن ترجمه‌شده"""
        return self.messages.get(key, key)