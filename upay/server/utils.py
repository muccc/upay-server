import threading
import logging
from functools import wraps

from . import app

global_lock = threading.RLock()


def get_global_lock(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with global_lock:
            return f(*args, **kwargs)
    return decorated


def initialize_logging():
    if 'LOGGING_CONFIG' in app.config:
        logging.config.fileConfig(app.config['LOGGING_CONFIG'])