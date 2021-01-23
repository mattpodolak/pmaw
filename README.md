<h2 align="center">PMAW: Pushshift Multithread API Wrapper</h2>

[![PyPI Version](https://img.shields.io/pypi/v/pmaw?color=blue)](https://pypi.org/project/pmaw/)
[![Python Version](https://img.shields.io/pypi/pyversions/pmaw?color=blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Description

**PMAW** is an ultra minimalist wrapper for the Pushshift API which uses multithreading to retrieve Reddit comments and submissions. General usage is through the `PushshiftAPI` class which provides methods for interacting with different `Pushshift` endpoints, please view the [Pushshift Docs](https://github.com/pushshift/api) for more details on the endpoints and accepted parameters. Parameters are provided through keyword arguments when calling the method, some methods will have required parameters. When using a method **PMAW** will complete all the required API calls to complete the query before returning an array of values, or in the case of `search_submission_comment_ids` a dictionary is returned mapping the submission id to an array of comment ids.

The following three methods are currently supported:

- Searching Comments: `search_comments`
  - [Details](https://github.com/pushshift/api#searching-comments)
- Search Submissions: `search_submissions`
  - [Details](https://github.com/pushshift/api#searching-submissions)
- Search Submission Comment IDs: `search_submission_comment_ids`
  - [Details](https://github.com/pushshift/api#get-all-comment-ids-for-a-particular-submission)

## Getting Started

### Installation

**PMAW** currently supports _Python 3.5_ or later. To install it via _pip_, run:

```sh
$ pip install pmaw
```

### General Usage

```python
from pmaw import PushshiftAPI()
api = PushshiftAPI(num_workers=5)
```

## Why Multithread?

When building large datasets from Reddit submission and comment data it can require thousands of API calls to the Pushshift API. The time it takes for your code to complete pulling all this data is limited by both your network latency and the response time of the Pushshift server, which can vary throughout the day.

Current API libraries such as PRAW and PSAW currently run requests sequentially, which can cause thousands of API calls to take many hours to complete. Since API requests are I/O-bound they can benefit from being run asynchronously using multiple threads. Implementing intelligent rate limiting can ensure that we minimize the number of rejected requests, and the time it takes to complete.

## Features

### Rate Limiting

**PMAW** intelligently rate limits the concurrent requests to the Pushshift server to reach your target provided rate.

Providing a `rate_limit` value is optional, this defaults to `60` requests per minute which is the recommended value for interacting with the Pushshift API. Increasing this value above `60` will increase the number of rejected requests and will increase the burden on the Pushshift server. A maximum recommended value is `100` requests per minute.

Additionally, the rate-limiting behaviour can be constrained by the `max_sleep` parameter which allows you to select a maximum period of time to sleep between requests.

### Multithreading

The number of threads to use during multithreading is set with the `num_workers` parameter. This is optional and defaults to `10`, however, you should provide a value as this may not be appropriate for your machine. Increasing the number of threads you use allows you to make more concurrent requests to Pushshift, however, the returns are diminishing as requests are constrained by the rate-limit. The optimal number of threads for requests is between `10` and `20` depending on the current response time of the Pushshift server.

When selecting the number of `threads` you can follow one of the two methodologies:

- Number of processors on the machine, multiplied by 5
- Minimum value of 32 and the number of processors plus 4

If you are unsure how many processors you have use: `os.cpu_count()`.

### Unsupported

- `asc` sort is unsupported
- searching for submissions or comments not by `id` is currently unsupported
- `aggs` are unsupported, as **PMAW** is intended to be used for collecting large numbers of submissions or comments. Use [PSAW](https://github.com/dmarx/psaw) for aggregation requests.

#### Features Requests

- For feature requests please open an issue with the `feature request` label, this will allow features to be better prioritized for future releases

# Examples

## Comments

### Search Comments by IDs

```python
comment_ids = ['gjacwx5','gjad2l6','gjadatw','gjadc7w','gjadcwh',
  'gjadgd7','gjadlbc','gjadnoc','gjadog1','gjadphb']
comments_arr = api.search_comments(ids=comment_ids)
```

You can supply a single comment by passing the id as a string or an array with a length of 1 to `ids`

[Detailed Example](https://github.com/mattpodolak/pmaw/blob/master/examples/search_comments.ipynb)

### Search Comment IDs by Submission ID

```python
post_ids = ['kxi2w8','kxi2g1','kxhzrl','kxhyh6','kxhwh0',
  'kxhv53','kxhm7b','kxhm3s','kxhg37','kxhak9']
comment_id_dict = api.search_submission_comment_ids(ids=post_ids)
```

You can supply a single submission by passing the id as a string or an array with a length of 1 to `ids`

[Detailed Example](https://github.com/mattpodolak/pmaw/blob/master/examples/search_submission_comment_ids.ipynb)

## Submission

### Search Submissions by IDs

```python
post_ids = ['kxi2w8','kxi2g1','kxhzrl','kxhyh6','kxhwh0',
  'kxhv53','kxhm7b','kxhm3s','kxhg37','kxhak9']
posts_arr = api.search_submissions(ids=post_ids)
```

You can supply a single submission by passing the id as a string or an array with a length of 1 to `ids`

[Detailed Example](https://github.com/mattpodolak/pmaw/blob/master/examples/search_submissions.ipynb)

## License

**PMAW** is released under the MIT License. See the
[LICENSE](https://github.com/mattpodolak/pmaw/blob/master/LICENSE) file for more
details.
