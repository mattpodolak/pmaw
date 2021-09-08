import logging
import time
import random

log = logging.getLogger(__name__)


class RateLimit(object):
    """RateLimit: Implements different rate-limiting strategies for concurrent requests"""

    def __init__(self, rate_limit=60, base_backoff=0.5, limit_type='average', max_sleep=60, jitter=None):
        self.rate_limit = rate_limit
        self.cache = list()
        self.base = base_backoff
        self.limit_type = limit_type
        self.max_sleep = max_sleep
        self.jitter = jitter
        self.sleep = self.base

        # track failures and attempts
        self.last_batch = 0
        self.attempts = 0
        self.num_fail = 0

    def delay(self):
        if self.limit_type:
            if self.limit_type == 'average':
                return min(self.max_sleep, self._average())
            elif self.limit_type == 'backoff':
                return self._backoff()
        else:
            return 0

    def _req_fail(self):
        self.num_fail += 1

    def _check_fail(self):
        # reset attempts if no new failures
        if self.last_batch == self.num_fail:
            self.num_fail = 0
            self.last_batch = 0
            self.attempts = 0
            self.sleep = self.base
        else:
            # store last batch num failures
            self.last_batch = self.num_fail

            # increase number of attempted batches
            self.attempts += 1

    def _expo(self):
        return min(self.max_sleep, self.base*pow(2, self.attempts))

    def _backoff(self):
        if self.jitter:
            if self.jitter == 'equal':
                v = self._expo()
                return v/2 + random.uniform(0, v/2)
            elif self.jitter == 'full':
                v = self._expo()
                return random.uniform(0, v)
            elif self.jitter == 'decorr':
                self.sleep = min(self.max_sleep, random.uniform(
                    self.base, self.sleep*3))
                return self.sleep
        else:
            return self._expo()

    def _average(self):
        # calculating delay required based on rate averaging
        curr_time = time.time()
        self.cache.append(curr_time)

        num_req = len(self.cache)
        first_req = min(self.cache)
        last_req = max(self.cache)

        # remove requests older than 60 seconds old
        while curr_time - first_req > 60:

            try:
                self.cache.remove(first_req)
            except ValueError:
                log.debug(f'{first_req} has already been removed RL cache')

            num_req = len(self.cache)
            first_req = min(self.cache)

        # return 0 if no other requests on cache
        if last_req == first_req:
            return 0
        else:
            period = last_req - first_req

            # project rate with no delay
            proj_rate = 60*(num_req)/(period)

            # check if projected rate is too high
            if(proj_rate < self.rate_limit or num_req < 5):
                return 0
            else:
                return 60*(num_req)/self.rate_limit - period
