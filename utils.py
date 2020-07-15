import hashlib
import time


def get_hash_for_url(url):
    return hashlib.md5(url.encode()).hexdigest()


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print(f'\033[1;32;40mFunction {method.__name__}() took {(te - ts) * 1000:2.2f}ms\033[00m')
        return result
    return timed
