import logging
import copy
import datetime as dt
from collections import deque
import warnings
from threading import Event
import signal
import time

from praw.exceptions import RedditAPIException

from pmaw.Cache import Cache
from pmaw.utils.slices import timeslice, mapslice
from pmaw.utils.filter import apply_filter
from pmaw.Response import Response


log = logging.getLogger(__name__)


class Request(object):
    """Request: Handles request information, response saving, and cache usage."""

    def __init__(self, payload, filter_fn, kind, max_results_per_request, max_ids_per_request, mem_safe, safe_exit, cache_dir=None, praw=None):
        self.kind = kind
        self.max_ids_per_request = min(500, max_ids_per_request)
        self.max_results_per_request = min(100, max_results_per_request)
        self.safe_exit = safe_exit
        self.mem_safe = mem_safe
        self.req_list = deque()
        self.payload = payload
        self.limit = payload.get('limit', None)
        self.exit = Event()
        self.praw = praw
        self._filter = filter_fn

        if filter_fn is not None and not callable(filter_fn):
            raise ValueError('filter_fn must be a callable function')

        if safe_exit and self.payload.get('before', None) is None:
            # warn the user not to use safe_exit without setting before,
            # doing otherwise will make it impossible to resume without modifying 
            # future query to use before value from first run
            before = int(dt.datetime.now().timestamp())
            payload['before'] = before
            warnings.warn(f'Using safe_exit without setting before value is not recommended. Setting before to {before}')

        if self.praw is not None:
            if safe_exit:
                raise NotImplementedError('safe_exit is not implemented when PRAW is used for metadata enrichment')

            self.enrich_list = deque()
            
            if not kind == 'submission_comment_ids' :
                # id filter causes an error for submission_comment_ids endpoint
                self.payload['filter'] = 'id'

            if kind == "submission":
                self.prefix = "t3_"
            else:
                self.prefix = "t1_"
            
        if 'ids' not in self.payload:
            # add necessary args
            self._add_nec_args(self.payload)

        if mem_safe or safe_exit:
            # instantiate cache
            _tmp = copy.deepcopy(payload)
            _tmp['kind'] = kind
            self._cache = Cache(_tmp, safe_exit, cache_dir=cache_dir)
            if safe_exit:
                info = self._cache.load_info()
                if info is not None:
                    self.req_list.extend(info['req_list'])
                    self.payload = info['payload']
                    self.limit = info['limit']
                    log.info(
                        f'Loaded Cache:: Responses: {self._cache.size} - Pending Requests: {len(self.req_list)} - Items Remaining: {self.limit}')
        else:
            self._cache = None

        # instantiate response
        self.resp = Response(self._cache)

    def check_sigs(self):
        try:
            getattr(signal, 'SIGHUP')
            sigs = ('TERM', 'HUP', 'INT')
        except AttributeError:
            sigs = ('TERM', 'INT')

        for sig in sigs:
            signal.signal(getattr(signal, 'SIG'+sig), self._exit)

    def _enrich_data(self):
        # create batch of fullnames up to 100
        fullnames = []
        while len(fullnames) < 100:
            try:
                fullnames.append(self.enrich_list.popleft())
            except IndexError:
                break
        
        # exit loop if nothing to enrich
        if len(fullnames) == 0:
            return
        
        try:
            # TODO: may need to change praw usage based on multithread performance
            resp_gen = self.praw.info(fullnames=fullnames)
            praw_data = [vars(obj) for obj in resp_gen]
            results = self._apply_filter(praw_data)
            self.resp.responses.extend(results)
            
        except RedditAPIException:
            self.enrich_list.extend(fullnames)

    def _idle_task(self, interval):
        start = time.time()
        current = time.time()

        if self.praw:
            # make multiple enrich requests based on sleep interval
            while current - start < interval and len(self.enrich_list) > 0:
                
                self._enrich_data()
                
                current = time.time()

        current = time.time()
        diff = (current - start)

        if diff < interval and diff >= 0:
            time.sleep(interval-diff)

    def save_cache(self):
        # trim extra responses
        self.trim()

        # enrich if needed
        if self.praw:
            while len(self.enrich_list) > 0:
                self._enrich_data()

        if self.safe_exit and not self.limit == None and (self.limit == 0 or self.exit.is_set()):
            # save request info to cache
            self._cache.save_info(req_list=self.req_list,
                                  payload=self.payload, limit=self.limit)
            # save responses to cache
            self.resp.to_cache()
        elif self.mem_safe:
            self.resp.to_cache()

    def _exit(self, signo, _frame):
        self.exit.set()

    def _apply_filter(self, results):
        # apply user defined filter function before storing
        if(self._filter is not None):
            return apply_filter(results, self._filter)
        else:
            return results    

    def save_resp(self, results):
        # dont filter results before updating limit: limit is the max number of results
        # extracted from Pushshift, filtering can reduce the results < limit
        if self.kind == 'submission_comment_ids':
            self.limit -= 1
        else:
            self.limit -= len(results)
            
        if self.praw:
            # save fullnames of objects to be enriched with metadata by PRAW
            if self.kind == 'submission_comment_ids':
                self.enrich_list.extend([self.prefix+res for res in results])
            else:
                self.enrich_list.extend([self.prefix+res['id'] for res in results])
        else:
            results = self._apply_filter(results)
            self.resp.responses.extend(results)

    def _add_nec_args(self, payload):
        """Adds arguments to the payload as necessary."""

        payload['size'] = self.max_results_per_request

        if 'sort' not in payload:
            payload['sort'] = 'desc'
        elif payload.get('sort') != 'desc':
            err_msg = "Support for non-default sort has not been implemented as it may cause unexpected results"
            raise NotImplementedError(err_msg)

        if 'metadata' not in payload:
            payload['metadata'] = 'true'
        if 'before' not in payload:
            payload['before'] = int(dt.datetime.now().timestamp())
        if 'filter' in payload:
            if not isinstance(payload['filter'], list):
                if isinstance(payload['filter'], str):
                    payload['filter'] = [payload['filter']]
                else:
                    payload['filter'] = list(payload['filter'])
            # make sure that the created_utc field is returned
            if 'created_utc' not in payload['filter']:
                payload['filter'].append('created_utc')

    def gen_slices(self, url, payload, after, before, num):
        # create time slices
        ts = timeslice(after, before, num)
        url_payloads = [(url, mapslice(copy.deepcopy(payload),
                                       ts[i], ts[i+1])) for i in range(num)]
        self.req_list.extend(url_payloads)

    def gen_url_payloads(self, url, batch_size, search_window):
        """Creates a list of url payload tuples"""
        url_payloads = []

        # check if new payloads have to be made
        if len(self.req_list) == 0:
            # paging for ids
            if 'ids' in self.payload:

                # convert ids to list
                self._id_list(self.payload)

                all_ids = self.payload['ids']
                if len(all_ids) == 0 and (self.limit and self.limit > 0):
                    warnings.warn(
                        f'{self.limit} items were not found in Pushshift')
                self.limit = len(all_ids)

                # remove ids from payload to prevent , -> %2C and increasing query length
                # beyond the max length of 8190
                self.payload['ids'] = []

                # if searching for submission comment ids
                if self.kind == "submission_comment_ids":
                    urls = [url+sub_id for sub_id in all_ids]
                    url_payloads = [(url, self.payload) for url in urls]
                else:
                    # split ids into arrays of size max_ids_per_request
                    ids_split = []
                    max_len = self.max_ids_per_request
                    while len(all_ids) > 0:
                        ids_split.append(",".join(all_ids[:max_len]))
                        all_ids = all_ids[max_len:]

                    log.debug(f'Created {len(ids_split)} id slices')

                    # create url payload tuples
                    url_payloads = [(url + '?ids=' + id_str, self.payload)
                                    for id_str in ids_split]
                # add payloads to req_list
                self.req_list.extend(url_payloads)

            else:
                if 'after' not in self.payload:
                    search_window = dt.timedelta(days=search_window)
                    num = batch_size
                    before = self.payload['before']
                    after = int((dt.datetime.fromtimestamp(
                        before) - search_window).timestamp())

                    # set before to after for future time slices
                    self.payload['before'] = after

                else:
                    before = self.payload['before']
                    after = self.payload['after']

                    # set before to avoid repeated time slices when there are missed responses
                    self.payload['before'] = after
                    num = batch_size

                # generate payloads
                self.gen_slices(
                    url, self.payload, after, before, num)

    def _id_list(self, payload):
        if not isinstance(payload['ids'], list):
            if isinstance(payload['ids'], str):
                payload['ids'] = [payload['ids']]
            else:
                payload['ids'] = list(payload['ids'])

    def trim(self):
        if self.limit:
            if self.praw:
                while self.limit < 0:
                    try:
                        self.enrich_list.pop()
                        self.limit += 1
                    except IndexError as exc:
                        break
            if self.limit < 0:
                log.debug(f'Trimming {self.limit*-1} requests')
                self.resp.responses = self.resp.responses[:self.limit]
                self.limit = 0
