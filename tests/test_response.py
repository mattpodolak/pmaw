from .config import tape, reddit, post_ids, comment_ids
from pmaw import Response, PushshiftAPI

@tape.use_cassette('test_submission_comment_ids_search')
def test_response_load_cache():
  api = PushshiftAPI(file_checkpoint=1)
  comments = api.search_submission_comment_ids(ids=post_ids, mem_safe=True)
  resp = Response.load_cache(key=comments._cache.key)
  assert(len(comments) == len(resp) and len(comments) == 66)

@tape.use_cassette('test_submission_comment_ids_search')
def test_response_generator():
  api = PushshiftAPI(file_checkpoint=1)
  comments = api.search_submission_comment_ids(ids=post_ids, mem_safe=True)
  all_c = [c for c in comments]
  assert(len(all_c) == 66)