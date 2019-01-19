

from config import settings
from concurrent.futures import ThreadPoolExecutor


class BaseService(object):
    executor = ThreadPoolExecutor(max_workers=16)

    def __init__(self, db_session):
        self._model = None
        self._debug_mode = settings.get("debug")
        self.db_session = db_session

    def set_debug_mode(self, mode):
        self._debug_mode = mode
