import os
import pickle
import json
import hashlib
import logging

log = logging.getLogger(__name__)


class Cache(object):
    def __init__(self, payload):
        # generating key
        key_str = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.key = hashlib.md5(key_str).hexdigest()
        print(f'Unique request key: {self.key}')

        self.checkpoint = 0

        # create cache folder
        self.folder = 'cache'
        try:
            os.mkdir(self.folder)
        except Exception as exc:
            log.debug(f'Folder creation failed - {exc}')

    def cache_responses(self, responses):
        self.checkpoint += 1
        print(f'Checkpoint {self.checkpoint}:: Caching Responses')

        filename = f'./{self.folder}/{self.checkpoint}-{self.key}.pickle'
        with open(filename, 'wb') as handle:
            pickle.dump(responses, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)

    def load_info(self):
        try:
            with open(f'./{self.folder}/{self.key}_info.pickle', 'rb') as handle:
                return pickle.load(handle)
        except:
            print('No previous requests to load')

    def save_info(self, **kwargs):
        filename = f'./{self.folder}/{self.key}_info.pickle'
        with open(filename, 'wb') as handle:
            pickle.dump(kwargs, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)
