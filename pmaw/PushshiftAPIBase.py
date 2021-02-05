import time
import pandas as pd
import datetime as dt
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import copy
import logging
import warnings

from pmaw.RateLimit import RateLimit

log = logging.getLogger(__name__)


class PushshiftAPIBase(object):
    _base_url = 'https://{domain}.pushshift.io/{{endpoint}}'

    def __init__(self, num_workers=10, max_sleep=60, rate_limit=60, base_backoff=0.5,
                 max_ids_per_request=1000, max_results_per_request=100, batch_size=None,
                 shards_down_behavior='warn', limit_type='average', jitter=None, search_window=365,
                 checkpoint=100):
        self.num_workers = num_workers
        self.domain = 'api'
        self.shards_down_behavior = shards_down_behavior
        self.max_ids_per_request = min(1000, max_ids_per_request)
        self.max_results_per_request = min(100, max_results_per_request)
        self.metadata_ = {}
        self.search_window = search_window
        self.resp_dict = {}
        self.checkpoint = checkpoint

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
            log.debug("Imposing rate limit, sleeping for %s" % interval)
            time.sleep(interval)

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
            raise Exception(f"HTTP {status} - {reason}")

    @property
    def shards_are_down(self):
        shards = self.metadata_.get('shards')
        if shards is None:
            return
        return shards['successful'] != shards['total']

    def _id_list(self, payload):
        if not isinstance(payload['ids'], list):
            if isinstance(payload['ids'], str):
                payload['ids'] = [payload['ids']]
            else:
                payload['ids'] = list(payload['ids'])

    def _gen_url_payloads(self, url, sub_c_id=False):
        """Creates a list of url payload tuples"""
        url_payloads = []
        url_dict = {}
        # paging for ids
        if 'ids' in self.payload:

            # convert ids to list
            self._id_list(self.payload)

            all_ids = self.payload['ids']

            # remove ids from payload to prevent , -> %2C and increasing query length
            # beyond the max length of 8190
            self.payload.pop('ids', None)

            # if searching for submission comment ids
            if sub_c_id:
                url_dict = {url+sub_id: sub_id for sub_id in all_ids}
                url_payloads = [(url, self.payload) for url in url_dict.keys()]
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
        else:
            if 'after' not in self.payload:
                search_window = dt.timedelta(days=self.search_window)
                num = self.num_workers
                before = self.payload['before']
                after = int((dt.datetime.fromtimestamp(
                    before) - search_window).timestamp())

                # set before to after for future time slices
                self.payload['before'] = after

                # create time slices
                ts = self._timeslice(after, before, num)
                url_payloads = [(url, self._mapslice(copy.deepcopy(
                    self.payload), ts[i], ts[i+1])) for i in range(num)]

            else:
                before = self.payload['before']
                after = self.payload['after']
                num = self.batch_size

                # create time slices
                ts = self._timeslice(after, before, num)
                url_payloads = [(url, self._mapslice(copy.deepcopy(
                    self.payload), ts[i], ts[i+1])) for i in range(num)]

        return url_payloads, url_dict

    def _timeslice(self, after, before, num):
        log.debug(
            f'Generating {num} slices between {after} and {before}')
        return [int((before-after)*i/num) + after for i in range(num+1)]

    def _mapslice(self, payload, after, before):
        payload['before'] = before
        payload['after'] = after
        return payload

    def _add_nec_args(self, payload):
        """Adds arguments to the payload as necessary."""
        payload['limit'] = self.max_results_per_request
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

    def _multithread(self, url_payloads, url_dict={}, limit=None):
        # multi-thread requests
        if url_dict:
            results = {}
        else:
            results = []
        executor = ThreadPoolExecutor(max_workers=self.num_workers)
        # initialize task list deque
        req_list = deque()
        req_list.extend(url_payloads)

        while len(req_list) > 0:
            # reset resp_dict which tracks remaining responses for timeslices
            self.resp_dict = {}

            # batch number of futures created to batch size
            reqs = []
            for i in range(min(len(req_list), self.batch_size)):
                reqs.append(req_list.popleft())

            futures = {executor.submit(
                self._get, url_pay[0], url_pay[1]): url_pay for url_pay in reqs}

            for future in as_completed(futures):
                url_pay = futures[future]
                self.num_req += 1
                try:
                    data = future.result()
                    self.num_suc += 1
                    url = url_pay[0]
                    payload = url_pay[1]

                    if url_dict:
                        _id = url_dict[url]
                        results[_id] = data
                    else:
                        results.extend(data)

                    # handle time slicing logic
                    if 'before' in payload and 'after' in payload:
                        before = payload['before']
                        after = payload['after']
                        log.debug(
                            f"Time slice from {after} - {before} returned {len(data)} results")
                        limit -= len(data)
                        log.info(f'Remaining limit {limit}')
                        if limit <= 0:
                            log.debug(
                                f'Cancelling {len(req_list)} unfinished requests')
                            req_list.clear()
                            break
                        remaining = self.resp_dict.get(
                            (after, before), None)
                        log.debug(
                            f'{remaining} results remaining for this time slice')

                        # number of timeslices is depending on remaining results
                        if remaining and remaining > self.max_results_per_request*2:
                            num = 2
                            # find minimum `created_utc` to set as the `before` parameter in next timeslices
                            for result in data:
                                # set before to the last item retrieved from the time slice
                                r_before = float(result['created_utc'])
                                if r_before < before:
                                    before = r_before
                        else:
                            num = 1

                        # generate timeslices and payloads
                        ts = self._timeslice(after, before, num)
                        url_payloads = [(url, self._mapslice(copy.deepcopy(
                            payload), ts[i], ts[i+1])) for i in range(num)]
                        req_list.extend(url_payloads)
                except Exception as exc:
                    log.debug(f"Request Failed -- {exc}")
                    self._rate_limit._req_fail()
                    req_list.appendleft(url_pay)

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
                        shards_down_message + f' {len(req_list)} unfinished requests.')

            self.num_batches += 1
            if (self.num_req % self.checkpoint == 0):
                print(
                    f'Checkpoint:: Success Rate: {(self.num_suc/self.num_req*100):.2f}% - Requests: {self.num_req} - Batches: {self.num_batches}')

        print(
            f'Total:: Success Rate: {(self.num_suc/self.num_req*100):.2f}% - Requests: {self.num_req} - Batches: {self.num_batches}')
        self._shutdown(executor)
        return results

    def _shutdown(self, exc, wait=False, cancel_futures=True):
        # shutdown executor
        try:
            exc.shutdown(wait=wait, cancel_futures=cancel_futures)
        except:
            # TODO: manually cancel pending futures
            exc.shutdown(wait=wait)

    def _search(self,
                kind,
                dataset='reddit',
                **kwargs):
        self.metadata_ = {}
        self.payload = copy.deepcopy(kwargs)

        # track requests for a search query
        self.num_suc = 0
        self.num_req = 0
        self.num_batches = 0

        # raise error if aggs are requested
        if 'aggs' in self.payload:
            err_msg = "Aggregations support for {} has not yet been implemented, please use the PSAW package for your request"
            raise NotImplementedError(err_msg.format(self.payload['aggs']))

        if 'sort' not in self.payload:
            self.payload['sort'] = 'desc'
        elif self.payload.get('sort') != 'desc':
            err_msg = "Support for non-default sort has not been implemented as it may cause unexpected results"
            raise NotImplementedError(err_msg)

        if kind == 'submission_comment_ids':
            endpoint = f'{dataset}/submission/comment_ids/'
        else:
            endpoint = f'{dataset}/{kind}/search'

        url = self.base_url.format(endpoint=endpoint)

        if 'ids' in self.payload:
            # create array of payloads
            url_payloads, url_dict = self._gen_url_payloads(
                url, sub_c_id=kind == 'submission_comment_ids')

            return self._multithread(url_payloads, url_dict)
        else:
            limit = self.payload.get('limit', None)

            all_results = []

            # add necessary args
            self._add_nec_args(self.payload)

            # check to see how many results are available
            self._get(url, self.payload)

            total_avail = self.metadata_.get(
                'total_results', 0) + self.metadata_.get('results_returned', 0)
            print(
                f'{total_avail} total results available for the selected parameters')

            if limit is None or (limit and total_avail < limit):
                print(f'Setting limit to {total_avail}')
                limit = total_avail

            # return all_results if pushshift repeatedly returns an empty array
            while limit > 0:
                # create array of payloads
                url_payloads, url_dict = self._gen_url_payloads(
                    url, sub_c_id=kind == 'submission_comment_ids')
                results = self._multithread(url_payloads, url_dict, limit)
                all_results.extend(results)
                limit -= len(results)

            if limit < 0:
                log.debug(f'Trimming {limit*-1} requests')
                return all_results[:limit]
            else:
                return all_results
