from .admin import setup_admin_handlers
from .music import setup_music_handlers
from .payment import setup_payment_handlers

def setup_handlers(application):
    """تنظیم تمام هندلرهای ربات"""
    setup_admin_handlers(application)
    setup_music_handlers(application)
    setup_payment_handlers(application)