from .admin import setup_admin_handlers
from .music import setup_music_handlers
from .payment import setup_payment_handlers

def setup_handlers(dispatcher):
    setup_admin_handlers(dispatcher)
    setup_music_handlers(dispatcher)
    setup_payment_handlers(dispatcher)