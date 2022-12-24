from pmaw import PushshiftAPI
from .config import tape, reddit
from .__mocks__.submission import ids_with_data as post_ids


@tape.use_cassette()
def test_submission_search_limit():
    api = PushshiftAPI(file_checkpoint=1)
    posts = api.search_submissions(subreddit="science", limit=100, until=1671827157)
    assert len(posts) == 100


@tape.use_cassette()
def test_submission_search_query():
    api = PushshiftAPI(file_checkpoint=1)
    posts = api.search_submissions(
        q="java", subreddit="programming", limit=100, until=1671827157
    )
    assert len(posts) == 100


@tape.use_cassette()
def test_submission_search_ids():
    api = PushshiftAPI(file_checkpoint=1)
    posts = api.search_submissions(ids=post_ids)
    # 6 out of 16 items not found (expected)
    assert len(posts) == 10


@tape.use_cassette()
def test_submission_search_mem_safe():
    api = PushshiftAPI(file_checkpoint=1)
    posts = api.search_submissions(
        subreddit="science",
        limit=1000,
        mem_safe=True,
        until=1671827157,
    )
    assert len(posts) == 1000


@tape.use_cassette()
def test_submission_praw_mem_safe():
    api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
    posts = api_praw.search_submissions(
        subreddit="programming", limit=1000, mem_safe=True, until=1671827157
    )
    assert len(posts) == 1000


@tape.use_cassette()
def test_submission_praw_limit():
    api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
    posts = api_praw.search_submissions(
        subreddit="programming", limit=100, until=1671827157
    )
    assert len(posts) == 100


@tape.use_cassette()
def test_submission_praw_query():
    api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
    posts = api_praw.search_submissions(
        q="ai", subreddit="programming", limit=100, until=1671827157
    )
    # TODO: why is 1 missing?
    assert len(posts) == 99


@tape.use_cassette()
def test_submission_praw_ids():
    api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
    posts = api_praw.search_submissions(ids=post_ids)
    # 6 out of 16 items not found (expected)
    assert len(posts) == 10
