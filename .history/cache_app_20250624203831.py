from flask_caching import Cache

def create_cache(app):
    cache = Cache(app)
    return cache