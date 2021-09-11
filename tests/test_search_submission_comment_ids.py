from .config import tape, reddit, post_ids
from pmaw import PushshiftAPI

@tape.use_cassette()
def test_submission_comment_ids_search():
  api = PushshiftAPI(file_checkpoint=1)
  comments = api.search_submission_comment_ids(ids=post_ids)
  assert(len(comments) == 66)

@tape.use_cassette()
def test_submission_comment_ids_praw():
  api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
  comments = api_praw.search_submission_comment_ids(ids=post_ids)
  assert(len(comments) == 66)

@tape.use_cassette('test_submission_comment_ids_search')
def test_submission_comment_ids_search_mem_safe():
  api = PushshiftAPI(file_checkpoint=1)
  comments = api.search_submission_comment_ids(ids=post_ids, mem_safe=True)
  assert(len(comments) == 66)

@tape.use_cassette('test_submission_comment_ids_praw')
def test_submission_comment_ids_praw_mem_safe():
  api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
  comments = api_praw.search_submission_comment_ids(ids=post_ids, mem_safe=True)
  assert(len(comments) == 66)