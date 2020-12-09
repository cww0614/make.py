import importlib.util
import sys

from .executor import Executor
from .filesystem import FileSystem
from .task import TASKS


def load_script(path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("Makefile", path)
    makefile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(makefile)


def main():
    load_script("Makefile.py")

    targets = sys.argv[1:]
    if len(targets) == 0:
        targets = ["all"]

    fs = FileSystem()
    Executor(fs, TASKS).execute(targets)


if __name__ == "__main__":
    main()
