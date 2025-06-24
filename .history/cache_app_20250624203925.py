from flask_caching import Cache




def __init__(app):
    """
    Initialize the Flask app with caching.
    
    Args:
        app: The Flask application instance.
    """
    cache = Cache(app, config={
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300  # Cache timeout in seconds
    })
    
    @app.route('/cache_test')
    @cache.cached(timeout=60)  # Cache this route for 60 seconds
    def cache_test():
        return "This is a cached response!"