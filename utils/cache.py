from cachetools import TTLCache
from config import Config

cache = TTLCache(maxsize=1000, ttl=300)

def init_cache():
    # Initialize cache with default values
    cache['rate_limit'] = {}

def check_rate_limit(user_id):
    if user_id in cache['rate_limit']:
        return False
    cache['rate_limit'][user_id] = True
    return True