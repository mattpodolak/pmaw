import logging

log = logging.getLogger(__name__)


def timeslice(after, before, num):
    log.debug(
        f'Generating {num} slices between {after} and {before}')
    return [int((before-after)*i/num + after) for i in range(num+1)]


def mapslice(payload, after, before):
    payload['before'] = before
    payload['after'] = after
    return payload
