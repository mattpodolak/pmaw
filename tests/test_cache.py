from pmaw import Cache

def test_no_info():
  cache = Cache({}, False, cache_dir='./rand_cache')
  info = cache.load_info()
  assert(info == None)