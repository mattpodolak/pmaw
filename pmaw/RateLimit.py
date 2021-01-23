import logging
import time

log = logging.getLogger(__name__)


class RateLimit(object):
    """
    We define a RateLimit object to manage the rate limit for concurrent requests

    Input:
        rate_limit (int, optional) - Maximum number of requests per minute, defaults to 60 requests per minute.
        limit_type (str, optional) - Type of rate limiting to use, default value is 'mean' for rate averaging
    """

    def __init__(self, rate_limit=60, limit_type='mean'):
        self.rate_limit = rate_limit
        self.cache = list()
        self.limit_type = limit_type

    def _rate_limit(self, period, num_req):
        if self.limit_type == 'mean':
            # calculating delay required based on rate averaging
            return 60*(num_req)/self.rate_limit - period
        else:
            return 0

    def req(self):
        curr_time = time.time()
        self.cache.append(curr_time)
        log.debug(f'Cache: {self.cache}- Current Time: {curr_time}')

        num_req = len(self.cache)
        first_req = min(self.cache)
        last_req = max(self.cache)

        # remove requests older than 60 seconds old
        while curr_time - first_req > 60:
            log.debug(
                f'Removing Time: {first_req} -- {curr_time} -- {first_req - curr_time}')
            try:
                self.cache.remove(first_req)
            except:
                log.info(f'{first_req} has already been removed')

            num_req = len(self.cache)
            first_req = min(self.cache)

        log.debug(
            f'Num {num_req} - {curr_time} - {last_req - first_req}')

        # return 0 if no other requests on cache
        if last_req == first_req:
            return 0
        else:
            period = last_req - first_req

            # project rate with no delay
            proj_rate = 60*(num_req)/(period)

            # check if projected rate is too high
            log.debug(f'Projected {proj_rate} -- Desired {self.rate_limit}')
            if(proj_rate < self.rate_limit):
                return 0
            else:
                return self._rate_limit(period, num_req)
