import logging

log = logging.getLogger(__name__)


def timeslice(since, until, num):
    log.debug(f"Generating {num} slices between {since} and {until}")
    return [int((until - since) * i / num + since) for i in range(num + 1)]


def mapslice(payload, since, until):
    payload["until"] = until
    payload["since"] = since
    return payload
