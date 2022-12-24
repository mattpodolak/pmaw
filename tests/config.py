import os

import vcr
import praw
from dotenv import load_dotenv

load_dotenv()

client_id = os.environ.get("REDDIT_CLIENT_ID")
client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

# dont record responses that werent successful, usually due to rate limiting
def bad_status(response):
    if response["status"]["code"] == 200:
        return response
    elif response["status"]["code"] == 404:
        # TODO: remove once submission comment ids endpoint is working
        return response
    else:
        return None


tape = vcr.VCR(
    match_on=["uri"],
    filter_headers=["Authorization"],
    cassette_library_dir="cassettes",
    record_mode="new_episodes",
    before_record_response=bad_status,
)

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent="python: PMAW v2 endpoint testing (by u/potato-sword)",
)
