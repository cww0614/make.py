import importlib.util
import sys
from argparse import ArgumentParser

from .executor import Executor, JobPool
from .filesystem import FileSystem
from .task import TASKS
from .persistence import STORAGE


def load_script(path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("makefile", path)
    makefile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(makefile)


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-j", "--jobs", type=int, default=1)
    arg_parser.add_argument("-f", "--file", default="Makefile.py")
    arg_parser.add_argument("targets", nargs="*", default=["all"])

    args = arg_parser.parse_args()
    load_script(args.file)

    STORAGE.load()
    try:
        for target in args.targets:
            fs = FileSystem()
            job_pool = JobPool()
            Executor(fs, job_pool, TASKS, jobs=args.jobs).execute(target)
    finally:
        STORAGE.dump()


if __name__ == "__main__":
    main()
