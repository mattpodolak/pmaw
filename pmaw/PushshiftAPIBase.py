import time
import pandas as pd
import datetime as dt
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, namedtuple
import copy
import logging
import warnings

from pmaw.RateLimit import RateLimit

log = logging.getLogger(__name__)


class PushshiftAPIBase(object):
    _base_url = 'https://{domain}.pushshift.io/{{endpoint}}'

    def __init__(self, max_retries=20, num_workers=10, max_sleep=60, rate_limit=60, max_results_per_request=1000, shards_down_behavior='warn', limit_type='mean'):
        self.max_retries = max_retries
        self.num_workers = num_workers
        self.threads = []
        self.domain = 'api'
        self.shards_down_behavior = shards_down_behavior
        self.max_results_per_request = min(1000, max_results_per_request)
        self.metadata_ = {}
        self.max_sleep = max_sleep

        # instantiate rate limiter
        self._rate_limit = RateLimit(rate_limit, limit_type)

    @property
    def base_url(self):
        # getter for base_url, with formatted domain
        return self._base_url.format(domain=self.domain)

    def _impose_rate_limit(self):
        interval = self._rate_limit.req()
        interval = min(interval, self.max_sleep)
        if interval > 0:
            log.debug("Imposing rate limit, sleeping for %s" % interval)
            time.sleep(interval)

    def _get(self, url, payload={}):
        self._impose_rate_limit()
        log.debug(f'Time of call: {time.time()}')
        r = requests.get(url, params=payload)
        status = r.status_code
        reason = r.reason

        if status == 200:
            r = json.loads(r.text)

            # check if shards are down
            self.metadata_ = r.get('metadata', {})
            self._shards_are_down()

            return r['data']
        else:
            raise Exception(f"HTTP {status} - {reason}")

    def _shards_are_down(self):
        shards = self.metadata_.get('shards')
        if shards is None:
            return
        if shards['successful'] != shards['total']:
            shards_down_message = "Not all PushShift shards are active. Query results may be incomplete"
            if self.shards_down_behavior == 'warn':
                log.warning(shards_down_message)
            if self.shards_down_behavior == 'stop':
                raise RuntimeError(shards_down_message)
        return

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
                # split ids into arrays of size max_results_per_request
                ids_split = []
                max_len = self.max_results_per_request
                while len(all_ids) > 0:
                    ids_split.append(",".join(all_ids[:max_len]))
                    all_ids = all_ids[max_len:]

                log.debug(f'Created {len(ids_split)} id slices')

                # create url payload tuples
                url_payloads = [(url + '?ids=' + id_str, self.payload)
                                for id_str in ids_split]

        return url_payloads, url_dict

    def _multithread(self, url_payloads, url_dict={}):
        # multi-thread requests
        if url_dict:
            results = {}
        else:
            results = []
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # initialize task list deque
            req_list = deque()
            req_list.extend(url_payloads)

            # track requests and successes
            num_req = 0
            num_suc = 0
            num_retries = 0
            shards = True  # set to false if shards are down and behaviour is set to stop
            while len(req_list) > 0 and num_retries < self.max_retries+1 and shards:
                futures = {executor.submit(
                    self._get, url_pay[0], url_pay[1]): url_pay for url_pay in req_list}
                req_list.clear()
                for future in as_completed(futures):
                    url_pay = futures[future]
                    num_req += 1
                    try:
                        data = future.result()
                        num_suc += 1

                        log.info(f"Saving Response")
                        if url_dict:
                            _id = url_dict[url_pay[0]]
                            results[_id] = data
                        else:
                            results.extend(data)
                    except RuntimeError as exc:
                        shards = False
                    except Exception as exc:
                        log.info(f"Request Failed -- {exc}")
                        req_list.append(url_pay)
                print(
                    f'Total Success Rate: {(num_suc/num_req*100):.2f}% -- Total Reqs: {num_req} -- Num Retries: {num_retries}')
                num_retries += 1
            if not shards:
                warnings.warn(
                    f'Exiting: {exc}. {len(req_list)} unfinished requests.')
            if(num_retries > self.max_retries):
                warnings.warn(
                    f'Exiting: Number of maximum retries exceeded. {len(req_list)} unfinished requests.')
        return results

    def _search(self,
                kind,
                dataset='reddit',
                **kwargs):
        self.metadata_ = {}
        self.payload = copy.deepcopy(kwargs)

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
            err_msg = "Non-id based search is not yet supported"
            raise NotImplementedError(err_msg)
