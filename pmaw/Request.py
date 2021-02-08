import logging
import copy
import datetime as dt

from pmaw.Cache import Cache
from pmaw.utils.slices import timeslice, mapslice
from collections import deque

log = logging.getLogger(__name__)


class Request(object):
    def __init__(self, payload, kind, max_results_per_request, max_ids_per_request, mem_safe, safe_exit):
        self.kind = kind
        self.max_ids_per_request = min(1000, max_ids_per_request)
        self.max_results_per_request = min(100, max_results_per_request)
        self.mem_safe = mem_safe
        self.safe_exit = safe_exit
        self.req_list = deque()
        self.payload = payload
        self.limit = payload.get('limit', None)
        self.response_cache = False  # track whether any responses are in cache
        self.num_checkpoint = 0
        self.results = []

        # instantiate cache
        _tmp = copy.deepcopy(payload)
        _tmp['kind'] = kind
        self._cache = Cache(_tmp)

        # TODO: load payload and req_list if self.key is in req_cache and req_list not equal to 0
        # TODO: set response_cache = True if responses are cached
        # TODO: set num_checkpoint if responses are cached
        # TODO: update limit
        info = self._cache.load_info()
        if info:
            self.req_list.extend(info['req_list'])
            self.payload = info['payload']
            self.limit = info['limit']
            print('Loaded previous request data')
            print(f'Limit {self.limit} - Payload: {self.payload}')

        if 'ids' not in self.payload:
            # add necessary args
            self._add_nec_args(self.payload)

    def save_cache(self):
        if self.mem_safe:
            self._cache.cache_responses(self.results)
            self.response_cache = True
            self.results.clear()
            if self.limit <= 0:
                # save request info to cache
                print('FInal save')

    @property
    def all_results(self):
        if self.response_cache:
            print('Loading from cache')
        else:
            return self.results

    def save_resp(self, results):
        self.results.extend(results)

    def _add_nec_args(self, payload):
        """Adds arguments to the payload as necessary."""

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
        return [(url, mapslice(copy.deepcopy(payload), ts[i], ts[i+1])) for i in range(num)]

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

                # remove ids from payload to prevent , -> %2C and increasing query length
                # beyond the max length of 8190
                payload = copy.deepcopy(self.payload)
                payload.pop('ids', None)

                # if searching for submission comment ids
                if self.kind == "submission_comment_ids":
                    urls = [url+sub_id for sub_id in all_ids]
                    url_payloads = [(url, payload) for url in urls]
                else:
                    # split ids into arrays of size max_ids_per_request
                    ids_split = []
                    max_len = self.max_ids_per_request
                    while len(all_ids) > 0:
                        ids_split.append(",".join(all_ids[:max_len]))
                        all_ids = all_ids[max_len:]

                    log.debug(f'Created {len(ids_split)} id slices')

                    # create url payload tuples
                    url_payloads = [(url + '?ids=' + id_str, payload)
                                    for id_str in ids_split]
            else:
                if 'after' not in self.payload:
                    search_window = dt.timedelta(days=search_window)
                    num = batch_size
                    before = self.payload['before']
                    after = int((dt.datetime.fromtimestamp(
                        before) - search_window).timestamp())

                    # set before to after for future time slices
                    self.payload['before'] = after

                    # generate payloads
                    url_payloads = self.gen_slices(
                        url, self.payload, after, before, num)

                else:
                    before = self.payload['before']
                    after = self.payload['after']
                    num = batch_size

                    # generate payloads
                    url_payloads = self.gen_slices(
                        url, self.payload, after, before, num)

            self.req_list.extend(url_payloads)

    def _id_list(self, payload):
        if not isinstance(payload['ids'], list):
            if isinstance(payload['ids'], str):
                payload['ids'] = [payload['ids']]
            else:
                payload['ids'] = list(payload['ids'])

    def trim(self):
        log.debug(f'Trimming {self.limit*-1} requests')
        self.results = self.results[:self.limit]
