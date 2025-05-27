MESSAGES = {
    'fa': {
        'welcome': 'سلام! خوش آمدید!',
        'enter_url': 'لطفاً لینک YouTube را ارسال کنید.',
        'download_error': 'مشکلی در دانلود موسیقی پیش آمد.',
        'payment_link': 'لینک پرداخت: {link}',
        'payment_failed': 'پرداخت ناموفق بود.',
    },
    'en': {
        'welcome': 'Hello! Welcome!',
        'enter_url': 'Please send the YouTube link.',
        'download_error': 'An error occurred while downloading the music.',
        'payment_link': 'Payment link: {link}',
        'payment_failed': 'Payment was unsuccessful.',
    }
}

def get_message(lang: str, key: str, **kwargs) -> str:
    return MESSAGES.get(lang, MESSAGES['fa']).get(key, '').format(**kwargs)
