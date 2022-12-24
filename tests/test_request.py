import pytest
from pmaw import PushshiftAPI
from .config import tape, reddit
from .__mocks__.comment import ids


@tape.use_cassette("test_comment_praw_ids")
def test_safe_exit_praw():
    with pytest.raises(NotImplementedError):
        api_praw = PushshiftAPI(praw=reddit)
        api_praw.search_comments(ids=ids, safe_exit=True)


@tape.use_cassette("test_comment_search_limit")
def test_asc_sort():
    with pytest.raises(NotImplementedError):
        api = PushshiftAPI()
        api.search_comments(
            subreddit="science", limit=100, until=1629990795, order="asc"
        )
