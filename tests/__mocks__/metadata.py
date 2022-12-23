# https://api.pushshift.io/reddit/comment/search?until=1629990795&track_total_hits=true&since=1629960795
before_after_query = {
    "es": {
      "took": 129,
      "timed_out": False,
      "_shards": {
        "total": 820,
        "successful": 820,
        "skipped": 816,
        "failed": 0
      },
      "hits": {
        "total": {
          "value": 2184259,
          "relation": "eq"
        },
        "max_score": None # null
      }
    },
    "es_query": {
      "track_total_hits": True,
      "size": 10,
      "query": {
        "bool": {
          "must": [
            {
              "bool": {
                "must": [
                  {
                    "range": {
                      "created_utc": {
                        "gte": 1629960795000
                      }
                    }
                  },
                  {
                    "range": {
                      "created_utc": {
                        "lt": 1629990795000
                      }
                    }
                  }
                ]
              }
            }
          ]
        }
      },
      "aggs": {},
      "sort": {
        "created_utc": "desc"
      }
    },
    "es_query2": "{\"track_total_hits\":true,\"size\":10,\"query\":{\"bool\":{\"must\":[{\"bool\":{\"must\":[{\"range\":{\"created_utc\":{\"gte\":1629960795000}}},{\"range\":{\"created_utc\":{\"lt\":1629990795000}}}]}}]}},\"aggs\":{},\"sort\":{\"created_utc\":\"desc\"}}",
    "api_launch_time": 1671472551.6688197,
    "api_request_start": 1671803683.826682,
    "api_request_end": 1671803685.9008527,
    "api_total_time": 2.0741705894470215
  }

# https://api.pushshift.io/reddit/submission/search?ids=zhzaea
submission_id = {
    "es": {
      "took": 14,
      "timed_out": False,
      "_shards": {
        "total": 4,
        "successful": 4,
        "skipped": 0,
        "failed": 0
      },
      "hits": {
        "total": {
          "value": 1,
          "relation": "eq"
        },
        "max_score": None # null
      }
    },
    "es_query": {
      "size": 10,
      "query": {
        "ids": {
          "values": [
            2146516066
          ]
        }
      },
      "aggs": {},
      "sort": {
        "created_utc": "desc"
      }
    },
    "es_query2": "{\"size\":10,\"query\":{\"ids\":{\"values\":[2146516066]}},\"aggs\":{},\"sort\":{\"created_utc\":\"desc\"}}"
  }

# synthetic
shards_down = {
    "es": {
      "took": 14,
      "timed_out": False,
      "_shards": {
        "total": 4,
        "successful": 2,
        "skipped": 0,
        "failed": 0
      },
      "hits": {
        "total": {
          "value": 1,
          "relation": "eq"
        },
        "max_score": None # null
      }
    },
    "es_query": {
      "size": 10,
      "query": {
        "ids": {
          "values": [
            2146516066
          ]
        }
      },
      "aggs": {},
      "sort": {
        "created_utc": "desc"
      }
    },
    "es_query2": "{\"size\":10,\"query\":{\"ids\":{\"values\":[2146516066]}},\"aggs\":{},\"sort\":{\"created_utc\":\"desc\"}}"
  }