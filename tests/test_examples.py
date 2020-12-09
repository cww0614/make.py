import os
import sys
from pathlib import Path
from subprocess import check_output

from make_py.__main__ import main
from make_py.task import TASKS

PROJ_ROOT = Path(__file__).parent.parent


def run_example(example, args=None):
    if args is None:
        args = []

    os.chdir(PROJ_ROOT / "examples" / example)
    TASKS.clear()
    sys.argv = ["_", *args]
    main()


def test_compile_c():
    run_example("compile_c")

    executable = Path(".") / "build" / "main"
    output = check_output([executable])
    assert output.strip() == b"Hello, World!"

    executable_ts = executable.stat().st_mtime

    (Path(".") / "hello.h").touch()

    run_example("compile_c")

    new_executable_ts = executable.stat().st_mtime
    assert new_executable_ts > executable_ts

    run_example("compile_c", ["clean"])
    assert not (Path(".") / "build").exists()


def test_file_concat():
    run_example("file_concat", ["example1-example2.txt"])

    assert (
        Path(".") / "example1-example2.txt"
    ).read_text() == "example1.txt\nexample2.txt\n"

    run_example("compile_c", ["clean"])
    assert list(Path(".").glob("*.txt")) == []
