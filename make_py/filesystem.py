from pathlib import Path


class FileSystem:
    def __init__(self):
        self.cache = {}

    def get_timestamp(self, path):
        time = self.cache.get(path)
        if time is not None:
            return time

        try:
            time = Path(path).stat().st_mtime
            self.cache[path] = time
            return time
        except Exception:
            return None

    @staticmethod
    def make_parents(path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
