import logging
from collections.abc import Generator

log = logging.getLogger(__name__)


class Response(Generator):
    """Response: A generator which contains the responses from the request, loads from cache if needed."""

    def __init__(self, cache=None):
        self.responses = []
        self._cache = cache
        # indexing for returning responses
        self.i = 0
        self.num_cache = 0

    def to_cache(self):
        self._cache.cache_responses(self.responses)
        self.responses.clear()

    def _next_resp(self):
        resp = self.responses[self.i]
        self.i += 1
        return resp

    def send(self, ignored_arg):
        if self.i < len(self.responses):
            return self._next_resp()
        elif self._cache and self.num_cache < len(self._cache.response_cache):
            self.responses = self._cache.load_resp(self.num_cache)
            self.num_cache += 1
            self.i = 0
            return self._next_resp()
        else:
            self.responses.clear()
            raise StopIteration

    def __del__(self):
        self.close()

    def throw(self, type=None, value=None, traceback=None):
        log.debug('Cleaning up responses')
        self.responses.clear()
        raise StopIteration

    def __len__(self):
        if self._cache:
            return len(self.responses) + self._cache.size
        else:
            return len(self.responses)
