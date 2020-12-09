import importlib.util
import sys
from argparse import ArgumentParser

from .executor import Executor
from .filesystem import FileSystem
from .task import TASKS


def load_script(path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("makefile", path)
    makefile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(makefile)


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-j", "--jobs", default=1)
    arg_parser.add_argument("-f", "--file", default="Makefile.py")
    arg_parser.add_argument("targets", nargs="*", default=["all"])

    args = arg_parser.parse_args()

    load_script(args.file)

    fs = FileSystem()
    for target in args.targets:
        Executor(fs, TASKS).execute(target)


if __name__ == "__main__":
    main()
