import psycopg2

class UserStats:
    def __init__(self, db_url):
        self.conn = psycopg2.connect(db_url)

    def get_user_count(self):
        """دریافت تعداد کل کاربران"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]

    def get_active_users(self, days=30):
        """دریافت تعداد کاربران فعال در یک بازه زمانی مشخص"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active >= NOW() - INTERVAL '%s days'", (days,))
            return cursor.fetchone()[0]