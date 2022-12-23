from .config import tape, reddit
from .__mocks__.submission import ids as post_ids 
from .__mocks__.comment import ids as comment_ids 
from pmaw import Response, PushshiftAPI

# TODO: add submission_comment_ids tests once endpoint is working again
# expected_length = 66
excepted_length = 0

@tape.use_cassette('test_submission_comment_ids_search')
def test_response_load_cache():
  api = PushshiftAPI(file_checkpoint=1)
  comments = api.search_submission_comment_ids(ids=post_ids, mem_safe=True)
  resp = Response.load_cache(key=comments._cache.key)
  assert(len(comments) == len(resp) and len(comments) == excepted_length)

@tape.use_cassette('test_submission_comment_ids_search')
def test_response_generator():
  api = PushshiftAPI(file_checkpoint=1)
  comments = api.search_submission_comment_ids(ids=post_ids, mem_safe=True)
  all_c = [c for c in comments]
  assert(len(all_c) == excepted_length)