from pmaw import PushshiftAPI
from .config import tape, reddit
from .__mocks__.submission import ids

# TODO: update submission_comment_ids tests once endpoint is working again
# expected_length = 66
expected_length = 0


@tape.use_cassette()
def test_submission_comment_ids_search():
    api = PushshiftAPI(file_checkpoint=1)
    comments = api.search_submission_comment_ids(ids=ids)
    assert len(comments) == expected_length


@tape.use_cassette()
def test_submission_comment_ids_praw():
    api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
    comments = api_praw.search_submission_comment_ids(ids=ids)
    assert len(comments) == expected_length


@tape.use_cassette("test_submission_comment_ids_search")
def test_submission_comment_ids_search_mem_safe():
    api = PushshiftAPI(file_checkpoint=1)
    comments = api.search_submission_comment_ids(ids=ids, mem_safe=True)
    assert len(comments) == expected_length


@tape.use_cassette("test_submission_comment_ids_praw")
def test_submission_comment_ids_praw_mem_safe():
    api_praw = PushshiftAPI(file_checkpoint=1, praw=reddit)
    comments = api_praw.search_submission_comment_ids(ids=ids, mem_safe=True)
    assert len(comments) == expected_length
