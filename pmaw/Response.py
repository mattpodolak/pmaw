import pandas as pd
import logging

log = logging.getLogger(__name__)


class Response(object):
    def __init__(self, cache, key):
        self.responses = []

    def as_list(self):
        return self.responses

    def as_df(self):
        return pd.DataFrame(self.responses)

    def save_csv(self, filename):
        pd.DataFrame(self.responses).to_csv(
            filename, header=True, index=False)
        print(f'Saved results to {filename}')
