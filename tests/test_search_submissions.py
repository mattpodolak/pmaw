from .config import tape, reddit, post_ids
from pmaw import PushshiftAPI

@tape.use_cassette()
def test_submission_search_limit():
  api = PushshiftAPI(file_checkpoint=1)
  posts = api.search_submissions(subreddit="science", limit=100, before=1629990795)
  assert(len(posts) == 100)

@tape.use_cassette()
def test_submission_praw_limit():
  api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
  posts = api_praw.search_submissions(subreddit="science", limit=100, before=1629990795)
  assert(len(posts) == 100)

@tape.use_cassette()
def test_submission_search_query():
  api = PushshiftAPI(file_checkpoint=1)
  posts = api.search_submissions(q="quantum", subreddit="science", limit=100, before=1629990795)
  assert(len(posts) == 100)

@tape.use_cassette()
def test_submission_praw_query():
  api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
  posts = api_praw.search_submissions(q="quantum", subreddit="science", limit=100, before=1629990795)
  assert(len(posts) == 100)

@tape.use_cassette()
def test_submission_search_ids():
  api = PushshiftAPI(file_checkpoint=1)
  posts = api.search_submissions(ids=post_ids)
  assert(len(posts) == len(post_ids))

@tape.use_cassette()
def test_submission_praw_ids():
  api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
  posts = api_praw.search_submissions(ids=post_ids)
  assert(len(posts) == len(post_ids))

@tape.use_cassette()
def test_submission_search_mem_safe():
  api = PushshiftAPI(file_checkpoint=1)
  posts = api.search_submissions(subreddit="science", limit=1000, mem_safe=True, before=1629990795)
  assert(len(posts) == 1000)

@tape.use_cassette()
def test_submission_praw_mem_safe():
  api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
  posts = api_praw.search_submissions(subreddit="science", limit=1000, mem_safe=True, before=1629990795)
  assert(len(posts) == 1000)