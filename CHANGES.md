## 2.0.0 (2021/09/xx)

- Added support for enriching result metadata using PRAW
- Implemented functional tests
- Reduced `max_ids_per_request` to 500
- Added automated testing

## 1.1.0 (2021/05/27)

- Added gzip for cached pickle files
- Exception handling is now slightly more specific
- Updated many print statements to output via logging
- Fixed issue with safe_exit not saving info

## 1.0.5 (2021/04/21)

- Moved remaining limit logging to DEBUG from INFO
- Fixed generator incorrect length after being partially iterated through
- Reduced the number of debug logs
- Fixed duplicate responses being returned if the number of responses for a provided window is less than expected

## 1.0.4 (2021/03/05)

- None type comparison bug fixed
- updated how limit was being updated for submission comment ids

## 1.0.3 (2021/02/19)

- fixed early cache bug
- fixed limit being retrieved from next search window when resuming from safe exit

## 1.0.2 (2021/02/16)

- fixed comments returning 25 by default

## 1.0.1 (2021/02/16)

- limit error in `trim` hot fix

## 1.0.0 (2021/02/14)

- `search` methods now return a `Response` generator object
- memory safety can now be enabled with `mem_safe` to cache responses during data retrieval and reduce the amount of memory used
- safe exiting can now be enabled with `safe_exit` to safely exit when an interrupt signal is received during data retrieval
- load unfinished requests and saved responses from `cache` when safe exiting is enabled
- request details are now handled inside a `Request` object

## 0.1.3 (2021/02/08)

- Fixed infinite while loop error
- Checkpoint by batch
- Removed erroneous pandas import

## 0.1.2 (2021/02/06)

- Fixed timeslicing creating extra requests

## 0.1.1 (2021/02/06)

- Fixed a bug with timeslicing causing duplicate results
- Fixed a miscalculation error for remaining results for a timeslice

## 0.1.0 (2021/02/05)

- General code improvements
- Added exponential backoff and jitter rate-limiting
- Added `non-id` search for submissions and comments

## 0.0.2 (2021/01/23)

- Initial implementation of multithreading requests for `ids` queries, with support for:
  - comment ids by submission id
  - submissions by id
  - comments by id
- Rate-limit based on rate averaging across previous requests
