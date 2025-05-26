from telegram import Bot

class NotificationManager:
    def __init__(self, bot_token):
        self.bot = Bot(bot_token)

    def send_notification(self, user_id, message):
        """ارسال اعلان به کاربر مشخص"""
        self.bot.send_message(chat_id=user_id, text=message)

    def send_bulk_notification(self, user_ids, message):
        """ارسال اعلان گروهی به کاربران"""
        for user_id in user_ids:
            self.send_notification(user_id, message)