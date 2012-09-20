try:
    # Python 2.7
    from logging import NullHandler
except ImportError:
    # Python < 2.7
    import logging
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass