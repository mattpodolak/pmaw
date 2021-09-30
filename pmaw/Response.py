import logging
from collections.abc import Generator

from pmaw.Cache import Cache

log = logging.getLogger(__name__)


class Response(Generator):
    """Response: A generator which contains the responses from the request, loads from cache if needed."""

    def __init__(self, cache=None):
        self.responses = []
        self._cache = cache
        # track length of remainder
        self.num_returned = 0
        # indexing for returning responses
        self.i = 0
        self.num_cache = 0
    
    @staticmethod
    def load_cache(key, cache_dir=None):
        """
        Return an instance of Response with the results stored with the provided key

        Input:
            key (str) - Cache key for results to load into Response
            cache_dir (str, optional) - An absolute or relative folder path to load cached responses from, defaults to './cache'
        Output:
            Response generator object
        """
        cache = Cache.load_with_key(key, cache_dir)
        return Response(cache)

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
            # increase num returned to reflect responses retrieved from cache
            # as well as previously returned responses
            self.num_returned += (self.i + len(self.responses))
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
            length = len(self.responses) + self._cache.size - (self.i + self.num_returned)
        else:
            length = len(self.responses) - self.i

        return max(length, 0)
