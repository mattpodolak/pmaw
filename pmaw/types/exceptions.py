from requests import HTTPError


class HTTPNotFoundError(HTTPError):
    """Error class for 404 error"""
