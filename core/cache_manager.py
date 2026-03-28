import json
import os
import hashlib

class CacheManager:
    def __init__(self, cache_dir="output/cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

    def get_hash(self, data):
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def is_cached(self, brief_data, engine):
        h = self.get_hash(brief_data)
        cache_file = os.path.join(self.cache_dir, f"{engine}_{h}.done")
        return os.path.exists(cache_file)

    def mark_done(self, brief_data, engine):
        h = self.get_hash(brief_data)
        with open(os.path.join(self.cache_dir, f"{engine}_{h}.done"), "w") as f:
            f.write("done")
