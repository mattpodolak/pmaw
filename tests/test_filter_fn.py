from .config import tape, reddit
from .__mocks__.comment import ids as comment_ids
from .__mocks__.submission import ids_with_data as post_ids
from pmaw import PushshiftAPI
import pytest


@tape.use_cassette("test_comment_praw_ids")
def test_praw_ids_filter():
    def fxn(item):
        return item["ups"] > 2

    api_praw = PushshiftAPI(praw=reddit)
    comments = api_praw.search_comments(ids=comment_ids, filter_fn=fxn)
    assert len(comments) == 4


@tape.use_cassette("test_submission_search_ids")
def test_search_ids_filter():
    api = PushshiftAPI()

    def fxn(item):
        return item["score"] > 2

    posts = api.search_submissions(ids=post_ids, filter_fn=fxn)
    assert len(posts) == 0


# TODO: add submission_comment_ids test once endpoint is working again
# @tape.use_cassette('test_submission_comment_ids_search')
# def test_submission_comment_id_exception():
#   with pytest.raises(ValueError):
#     api = PushshiftAPI()
#     def fxn(item):
#       return item['score'] > 2
#     api.search_submission_comment_ids(ids=post_ids, filter_fn=fxn)


@tape.use_cassette("test_submission_search_ids")
def test_filter_callable():
    with pytest.raises(ValueError):
        api = PushshiftAPI()
        api.search_submissions(ids=post_ids, filter_fn="fxn")


@tape.use_cassette("test_submission_search_ids")
def test_filter_param_exception():
    with pytest.raises(TypeError):
        api = PushshiftAPI()

        def fxn():
            return True

        api.search_submissions(ids=post_ids, filter_fn=fxn)


@tape.use_cassette("test_submission_search_ids")
def test_filter_key_exception():
    with pytest.raises(KeyError):
        api = PushshiftAPI()

        def fxn(item):
            return item["badkeydoesntexist"] > 2

        api.search_submissions(ids=post_ids, filter_fn=fxn)
