import json
from pathlib import Path


class StorageManager:
    def __init__(self):
        self.storages = {}

    def load(self):
        for path, storage in self.storages.items():
            try:
                with open(path) as f:
                    storage.update(json.load(f))
            except FileNotFoundError:
                storage.clear()

    def dump(self):
        for path, storage in self.storages.items():
            if len(storage) == 0 and not path.exists():
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w+") as f:
                json.dump(storage, f)

    def get_storage(self, path):
        abs_path = Path(path).resolve()
        storage = self.storages.get(abs_path)
        if storage:
            return abs_path, storage

        storage = {}
        self.storages[abs_path] = storage
        return abs_path, storage


STORAGE = StorageManager()


class PersistentVariables:
    def __init__(self, filename):
        self.path, self.storage = STORAGE.get_storage(filename)

    def __getitem__(self, item):
        return VariableProxy(self.storage, item)

    def clear(self):
        self.storage.clear()


class VariableProxy:
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name

    def get(self):
        return self.storage[self.name]

    def get_default(self, default):
        return self.storage.get(self.name, default)

    def set(self, value):
        self.storage[self.name] = value
