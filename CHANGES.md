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
