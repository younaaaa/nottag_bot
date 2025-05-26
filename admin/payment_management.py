import psycopg2

class PaymentManager:
    def __init__(self, db_url):
        self.conn = psycopg2.connect(db_url)

    def get_user_payments(self, user_id):
        """دریافت لیست پرداخت‌های کاربر"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM payments WHERE user_id = %s", (user_id,))
            return cursor.fetchall()

    def get_total_revenue(self):
        """محاسبه درآمد کلی سیستم"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT SUM(amount) FROM payments")
            return cursor.fetchone()[0]