import os

import vcr
import praw
from dotenv import load_dotenv

load_dotenv()

client_id = os.environ.get('REDDIT_CLIENT_ID')
client_secret = os.environ.get('REDDIT_CLIENT_SECRET')

# dont record responses that werent successful, usually due to rate limiting
def bad_status(response):
    if(response['status']['code'] == 200):
      return response
    else:
      return None


tape = vcr.VCR(
  match_on=['uri'],
  filter_headers=['Authorization'],
  cassette_library_dir='cassettes',
  record_mode='new_episodes',
  before_record_response=bad_status,
)

reddit = praw.Reddit(
 client_id=client_id,
 client_secret=client_secret,
 user_agent=f'python: PMAW v2 endpoint testing (by u/potato-sword)'
)

post_ids = [
  'kxi2w8',
  'kxi2g1',
  'kxhzrl',
  'kxhyh6',
  'kxhwh0',
  'kxhv53',
  'kxhm7b',
  'kxhm3s',
  'kxhg37',
  'kxhak9'
]

comment_ids = [
  'gjacwx5',
  'gjad2l6',
  'gjadatw',
  'gjadc7w',
  'gjadcwh',
  'gjadgd7',
  'gjadlbc',
  'gjadnoc',
  'gjadog1',
  'gjadphb'
]
