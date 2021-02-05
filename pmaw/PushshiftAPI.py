import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from collections import deque
import logging

from pmaw.PushshiftAPIBase import PushshiftAPIBase

log = logging.getLogger(__name__)


class PushshiftAPI(PushshiftAPIBase):
    def __init__(self, *args, **kwargs):
        """
        Helper class for interacting with the PushShift API for searching public reddit archival data using multiple threads.

        Input: 

            num_workers (int, optional) - Number of workers to use for multithreading, defaults to 10.

            max_sleep (int, optional) - Maximum rate-limit sleep time (in seconds) between requests, defaults to 60s.

            rate_limit (int, optional) - Target number of requests per minute for rate-averaging, defaults to 60 requests per minute.

            base_backoff (float, optional) - Base delay in seconds for exponential backoff, defaults to 0.5s

            max_ids_per_request (int, optional) - Maximum number of ids to use in a single request, defaults to 1000, maximum 1000.

            max_results_per_request (int, optional) - Maximum number of items to return in a single non-id based request, defaults to 100, maximum 100.

            batch_size (int, optional) - Size of batches for multithreading, defaults to number of workers.

            shards_down_behavior (str, optional) - Specifies how PMAW will respond if some shards are down during a query. Options are "warn" to only emit a warning, "stop" to throw a RuntimeError, or None to take no action. Defaults to "warn".

            limit_type (str, optional) - Type of rate limiting to use, default value is 'average' for rate averaging, use 'backoff' for exponential backoff

            jitter (str, optional) - Jitter to use with backoff, defaults to None, options are None, full, equal, decorr

            search_window (int, optional) - Size in days for search window for submissions / comments in non-id based search, defaults to 365

            checkpoint (int, optional) - Size of interval in requests to print a checkpoint with stats, defaults to 100
        """
        super().__init__(*args, **kwargs)

    def search_submission_comment_ids(self, ids, **kwargs):
        """
        Method for getting comment ids based on submission id(s)

        Input:
            ids (str, list) - Submission id(s) to return the comment ids of

        Output:
            dictionary with the format - {submission_id: comments_array}
        """
        kwargs['ids'] = ids
        return self._search(kind='submission_comment_ids', **kwargs)

    def search_comments(self, **kwargs):
        """
        Method for searching comments, returns an array of comments

        Output:
            array of comments in dictionary format
        """
        return self._search(kind='comment', **kwargs)

    def search_submissions(self, **kwargs):
        """
        Method for searching submissions, returns an array of submissions

        Output:
            array of submissions in dictionary format
        """
        return self._search(kind='submission', **kwargs)
