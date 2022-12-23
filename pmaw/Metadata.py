from typing import Optional, Tuple

"""
Helper class for working with request metadata
"""



class Metadata:
    def __init__(self, metadata) -> None:
        self._metadata = metadata

    @property
    def shards_are_down(self) -> bool:
        try:
            shards = self._metadata['es'].get('_shards')
        except KeyError:
            return True

        if shards is None:
            return True

        return shards['successful'] != shards['total']
    
    @property
    def total_results(self) -> int:
        try:
            return self._metadata['es']['hits']['total']['value']
        except KeyError:
            return 0
    
    @property
    def ranges(self) -> Tuple[Optional[int], Optional[int]]:
        after, before = None, None
        query_params = self._metadata['es_query']['query'].get('bool', None)

        # if searching by ids before and after timestamps wont exist
        # in the metadata, and instead look like ['query']['ids']
        if query_params:
            # now we have to find the before and after values
            for condition in query_params['must']:
                if 'bool' in condition and 'must' in condition['bool']:
                    for nested_cond in condition['bool']['must']:
                        if 'range' in nested_cond and 'created_utc' in nested_cond['range']:
                            # either before or after
                            timestamp = nested_cond['range']['created_utc']
                            if 'gte' in timestamp:
                                after = timestamp['gte']
                            elif 'lt' in timestamp:
                                before = timestamp['lt']
        return after, before