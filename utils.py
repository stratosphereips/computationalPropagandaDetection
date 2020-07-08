import hashlib


def get_hash_for_url(url):
    return hashlib.md5(url.encode()).hexdigest()

