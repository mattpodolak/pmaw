import json
import copy
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests import HTTPError

from pmaw.RateLimit import RateLimit
from pmaw.Request import Request

logging.basicConfig(level = logging.INFO, stream=sys.stdout)
log = logging.getLogger(__name__)

class PushshiftAPIBase(object):
    _base_url = 'https://{domain}.pushshift.io/{{endpoint}}'

    def __init__(self, num_workers=10, max_sleep=60, rate_limit=60, base_backoff=0.5,
                 batch_size=None, shards_down_behavior='warn', limit_type='average', jitter=None,
                 checkpoint=10, file_checkpoint=20, praw=None):
        self.num_workers = num_workers
        self.domain = 'api'
        self.shards_down_behavior = shards_down_behavior
        self.metadata_ = {}
        self.resp_dict = {}
        self.checkpoint = checkpoint
        self.file_checkpoint = file_checkpoint
        self.praw = praw

        if batch_size:
            self.batch_size = batch_size
        else:
            self.batch_size = num_workers

        # instantiate rate limiter
        self._rate_limit = RateLimit(
            rate_limit, base_backoff, limit_type, max_sleep, jitter)

    @property
    def base_url(self):
        # getter for base_url, with formatted domain
        return self._base_url.format(domain=self.domain)

    def _impose_rate_limit(self):
        interval = self._rate_limit.delay()
        if interval > 0:
            self.req._idle_task(interval)

    def _get(self, url, payload={}):
        self._impose_rate_limit()
        r = requests.get(url, params=payload)
        status = r.status_code
        reason = r.reason

        if status == 200:
            r = json.loads(r.text)

            # check if shards are down
            self.metadata_ = r.get('metadata', {})
            total_results = self.metadata_.get('total_results', None)
            if total_results:
                after, before = None, None
                for param in self.metadata_['ranges']:
                    created = param['range']['created_utc']
                    if created.get('gt', None):
                        after = created['gt']
                    elif created.get('lt', None):
                        before = created['lt']
                if after and before:
                    self.resp_dict[(after, before)] = total_results

            return r['data']
        else:
            raise HTTPError(f"HTTP {status} - {reason}")

    @property
    def shards_are_down(self):
        shards = self.metadata_.get('shards')
        if shards is None:
            return
        return shards['successful'] != shards['total']

    def _multithread(self, check_total=False):
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:

            while len(self.req.req_list) > 0 and not self.req.exit.is_set():
                # reset resp_dict which tracks remaining responses for timeslices
                self.resp_dict = {}

                # set number of futures created to batch size
                reqs = []
                if check_total:
                    reqs.append(self.req.req_list.popleft())
                else:
                    for i in range(min(len(self.req.req_list), self.batch_size)):
                        reqs.append(self.req.req_list.popleft())

                futures = {executor.submit(
                    self._get, url_pay[0], url_pay[1]): url_pay for url_pay in reqs}

                self._futures_handler(futures, check_total)

                # reset attempts if no failures
                self._rate_limit._check_fail()

                # check if shards are down
                if self.shards_are_down and (self.shards_down_behavior is not None):
                    shards_down_message = "Not all PushShift shards are active. Query results may be incomplete."
                    if self.shards_down_behavior == 'warn':
                        log.warning(shards_down_message)
                    if self.shards_down_behavior == 'stop':
                        self._shutdown(executor)
                        raise RuntimeError(
                            shards_down_message + f' {len(self.req.req_list)} unfinished requests.')
                if not check_total:
                    self.num_batches += 1
                    if self.num_batches % self.file_checkpoint == 0:
                        # cache current results
                        executor.submit(self.req.save_cache())
                    self._print_stats('Checkpoint')
                else:
                    break
            if not check_total:
                self._print_stats('Total')
            self._shutdown(executor)

    def _futures_handler(self, futures, check_total):
        for future in as_completed(futures):
            url_pay = futures[future]
            self.num_req += int(not check_total)
            try:
                data = future.result()
                self.num_suc += int(not check_total)
                url = url_pay[0]
                payload = url_pay[1]
                if not check_total:
                    self.req.save_resp(data)

                    log.debug(f'Remaining limit {self.req.limit}')
                    if self.req.limit <= 0:
                        log.debug(
                            f'Cancelling {len(self.req.req_list)} unfinished requests')
                        self.req.req_list.clear()
                        break

                    # handle time slicing logic
                    if 'before' in payload and 'after' in payload:
                        before = payload['before']
                        after = payload['after']
                        log.debug(
                            f"Time slice from {after} - {before} returned {len(data)} results")
                        total_results = self.resp_dict.get(
                            (after, before), 0)
                        log.debug(
                            f'{total_results} total results for this time slice')
                        # calculate remaining results
                        remaining = total_results - len(data)

                        # number of timeslices is depending on remaining results
                        if remaining > self.req.max_results_per_request*2:
                            num = 2
                        elif remaining > 0:
                            num = 1
                        else:
                            num = 0

                        if num > 0:
                            # find minimum `created_utc` to set as the `before` parameter in next timeslices
                            before = data[-1]['created_utc']

                            # generate payloads
                            self.req.gen_slices(
                                url, payload, after, before, num)
            except HTTPError as exc:
                log.debug(f"Request Failed -- {exc}")
                self._rate_limit._req_fail()
                self.req.req_list.appendleft(url_pay)

    def _shutdown(self, exc, wait=False, cancel_futures=True):
        # shutdown executor
        try:
            # pass cancel_futures keywords avail in python 3.9
            exc.shutdown(wait=wait, cancel_futures=cancel_futures)
        except TypeError:
            # TODO: manually cancel pending futures
            exc.shutdown(wait=wait)

    def _print_stats(self, prefix):
        rate = self.num_suc/self.num_req*100
        remaining = self.req.limit
        if (self.num_batches % self.checkpoint == 0) and prefix == 'Checkpoint':
            log.info(
                f'{prefix}:: Success Rate: {rate:.2f}% - Requests: {self.num_req} - Batches: {self.num_batches} - Items Remaining: {remaining}')
        elif prefix == 'Total':
            if remaining < 0:
                remaining = 0  # don't print a neg number
            log.info(
                f'{prefix}:: Success Rate: {rate:.2f}% - Requests: {self.num_req} - Batches: {self.num_batches} - Items Remaining: {remaining}')
            if(self.req.praw and len(self.req.enrich_list) > 0):
                # let the user know praw enrichment is still in progress so it doesnt appear to hang after
                # finishing retrieval from Pushshift
                log.info(f'Finishing enrichment for {len(self.req.enrich_list)} items')

    def _reset(self):
        self.num_suc = 0
        self.num_req = 0
        self.num_batches = 0

    def _search(self,
                kind,
                max_ids_per_request=500,
                max_results_per_request=100,
                mem_safe=False,
                search_window=365,
                dataset='reddit',
                safe_exit=False,
                cache_dir=None,
                filter_fn=None,
                **kwargs):

        # raise error if aggs are requested
        if 'aggs' in kwargs:
            err_msg = "Aggregations support for {} has not yet been implemented, please use the PSAW package for your request"
            raise NotImplementedError(err_msg.format(kwargs['aggs']))

        self.metadata_ = {}
        self.resp_dict = {}
        self.req = Request(copy.deepcopy(kwargs), filter_fn, kind,
                           max_results_per_request, max_ids_per_request, mem_safe, safe_exit, cache_dir, self.praw)

        # reset stat tracking
        self._reset()

        if kind == 'submission_comment_ids':
            endpoint = f'{dataset}/submission/comment_ids/'
        else:
            endpoint = f'{dataset}/{kind}/search'

        url = self.base_url.format(endpoint=endpoint)

        while (self.req.limit is None or self.req.limit > 0) and not self.req.exit.is_set():
            # set/update limit
            if 'ids' not in self.req.payload and len(self.req.req_list) == 0:
                # check to see how many results are remaining
                self.req.req_list.appendleft((url, self.req.payload))
                self._multithread(check_total=True)
                total_avail = self.metadata_.get('total_results', 0)

                if self.req.limit is None:
                    log.info(f'{total_avail} result(s) available in Pushshift')
                    self.req.limit = total_avail
                elif (total_avail < self.req.limit):
                    log.info(f'{self.req.limit - total_avail} result(s) not found in Pushshift')
                    self.req.limit = total_avail

            # generate payloads
            self.req.gen_url_payloads(
                url, self.batch_size, search_window)

            # check for exit signals
            self.req.check_sigs()

            if self.req.limit > 0 and len(self.req.req_list) > 0:
                self._multithread()

        self.req.save_cache()
        return self.req.resp
