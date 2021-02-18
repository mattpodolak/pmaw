import logging
import copy
import datetime as dt
from collections import deque
import warnings

from pmaw.Cache import Cache
from pmaw.utils.slices import timeslice, mapslice
from pmaw.Response import Response
from threading import Event
import signal

log = logging.getLogger(__name__)


class Request(object):
    """Request: Handles request information, response saving, and cache usage."""

    def __init__(self, payload, kind, max_results_per_request, max_ids_per_request, mem_safe, safe_exit):
        self.kind = kind
        self.max_ids_per_request = min(1000, max_ids_per_request)
        self.max_results_per_request = min(100, max_results_per_request)
        self.safe_exit = safe_exit
        self.mem_safe = mem_safe
        self.req_list = deque()
        self.payload = payload
        self.limit = payload.get('limit', None)
        self.exit = Event()

        if 'ids' not in self.payload:
            # add necessary args
            self._add_nec_args(self.payload)

        if mem_safe or safe_exit:
            # instantiate cache
            _tmp = copy.deepcopy(payload)
            _tmp['kind'] = kind
            self._cache = Cache(_tmp, safe_exit)
            if safe_exit:
                info = self._cache.load_info()
                if info:
                    self.req_list.extend(info['req_list'])
                    self.payload = info['payload']
                    self.limit = info['limit']
                    print(
                        f'Loaded Cache:: Responses: {self._cache.size} - Pending Requests: {len(self.req_list)} - Items Remaining: {self.limit}')
        else:
            self._cache = None

        # instantiate response
        self.resp = Response(self._cache)

    def check_sigs(self):
        try:
            getattr(signal, 'SIGHUP')
            sigs = ('TERM', 'HUP', 'INT')
        except:
            sigs = ('TERM', 'INT')

        for sig in sigs:
            signal.signal(getattr(signal, 'SIG'+sig), self._exit)

    def save_cache(self):
        # trim extra responses
        self.trim()
        if self.safe_exit and self.limit and (self.limit == 0 or self.exit.is_set()):
            # save request info to cache
            self._cache.save_info(req_list=self.req_list,
                                  payload=self.payload, limit=self.limit)
            # save responses to cache
            self.resp.to_cache()
        elif self.mem_safe:
            self.resp.to_cache()

    def _exit(self, signo, _frame):
        self.exit.set()

    def save_resp(self, results):
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
                if len(all_ids) == 0 and self.limit > 0:
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
        if self.limit and self.limit < 0:
            log.debug(f'Trimming {self.limit*-1} requests')
            self.resp.responses = self.resp.responses[:self.limit]
