from pmaw import Metadata
from .__mocks__ import metadata as mock_data


def test_before_after_query():
    metadata = Metadata(mock_data.before_after_query)
    total_results = metadata.total_results
    after, before = metadata.ranges
    assert after == 1629960795 and before == 1629990795
    assert total_results == 2184259


def test_submission_id():
    metadata = Metadata(mock_data.submission_id)
    total_results = metadata.total_results
    after, before = metadata.ranges
    assert before == None and after == None
    assert total_results == 1


def test_shards_down():
    metadata = Metadata(mock_data.shards_down)
    assert metadata.shards_are_down


def test_shards_not_down():
    metadata = Metadata(mock_data.submission_id)
    assert not metadata.shards_are_down
