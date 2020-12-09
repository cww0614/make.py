import pytest

from make_py.executor import Executor
from make_py.matcher import RegularExpressionMatcher, PlainTextMatcher
from make_py.task import Task


class TestFileSystem:
    def __init__(self, fs):
        self.fs = fs

    def get_timestamp(self, path):
        parts = path.split("/")
        node = self.fs
        for part in parts:
            next_node = node.get(part)
            if not next_node:
                return None

            node = next_node

        return node

    @staticmethod
    def make_parents(path):
        pass


TestFileSystem.__test__ = False


def fake_compile_tasks():
    compiled_files = []
    linked_files = []

    def compile(ctx):
        compiled_files.append((ctx.target, ctx.sources))

    def link(ctx):
        linked_files.append((ctx.target, ctx.sources))

    return (
        [
            Task(
                matcher=RegularExpressionMatcher(target="(.*).o", sources=["{}.c"]),
                handler=compile,
            ),
            Task(
                matcher=RegularExpressionMatcher(
                    target="binary", sources=[f"test{i}.o" for i in range(2)]
                ),
                handler=link,
            ),
            Task(
                matcher=PlainTextMatcher(target="test", sources=["binary"]),
                handler=lambda x: None,
                phony=True,
            ),
        ],
        compiled_files,
        linked_files,
    )


@pytest.mark.parametrize("fs_config", [{"test.c": 100}, {"test.c": 100, "test.o": 50}])
def test_recompile(fs_config):
    fs = TestFileSystem(fs_config)
    tasks, compiled, linked = fake_compile_tasks()

    executor = Executor(fs, tasks, silent=True)
    executor.execute("test.o")

    assert compiled == [("test.o", ["test.c"])]
    assert linked == []


def test_dont_recompile():
    fs = TestFileSystem({"test.c": 100, "test.o": 110})
    tasks, compiled, linked = fake_compile_tasks()

    executor = Executor(fs, tasks, silent=True)
    executor.execute("test.o")

    assert compiled == []
    assert linked == []


@pytest.mark.parametrize(
    "fs_config",
    [
        {
            "test0.c": 100,
            "test1.c": 100,
        },
        {
            "test0.c": 100,
            "test1.c": 100,
            "binary": 90,
        },
        {
            "test0.c": 100,
            "test1.c": 100,
            "binary": 110,
        },
    ],
)
def test_relink(fs_config):
    fs = TestFileSystem(fs_config)

    tasks, compiled, linked = fake_compile_tasks()

    executor = Executor(fs, tasks, silent=True)
    executor.execute("binary")

    assert compiled == [("test0.o", ["test0.c"]), ("test1.o", ["test1.c"])]
    assert linked == [("binary", ["test0.o", "test1.o"])]


@pytest.mark.parametrize(
    "fs_config,expected_compiled",
    [
        (
            {
                "test0.c": 130,
                "test1.c": 100,
                "test0.o": 110,
                "test1.o": 110,
                "binary": 120,
            },
            [("test0.o", ["test0.c"])],
        ),
        (
            {
                "test0.c": 100,
                "test1.c": 100,
                "test0.o": 110,
                "test1.o": 110,
                "binary": 90,
            },
            [],
        ),
        (
            {
                "test0.c": 100,
                "test1.c": 130,
                "test0.o": 110,
                "test1.o": 110,
                "binary": 120,
            },
            [("test1.o", ["test1.c"])],
        ),
    ],
)
def test_partial_relink(fs_config, expected_compiled):
    fs = TestFileSystem(fs_config)

    tasks, compiled, linked = fake_compile_tasks()

    executor = Executor(fs, tasks, silent=True)
    executor.execute("binary")

    assert compiled == expected_compiled
    assert linked == [("binary", ["test0.o", "test1.o"])]


@pytest.mark.parametrize(
    "fs_config,target",
    [
        (
            {
                "test0.c": 100,
                "test1.c": 100,
                "test0.o": 110,
                "test1.o": 110,
                "binary": 120,
            },
            "binary",
        ),
        (
            {
                "test0.c": 100,
                "test1.c": 100,
                "test0.o": 110,
                "test1.o": 110,
                "binary": 120,
            },
            "test",
        ),
    ],
)
def test_dont_relink(fs_config, target):
    fs = TestFileSystem(fs_config)

    tasks, compiled, linked = fake_compile_tasks()

    executor = Executor(fs, tasks, silent=True)
    executor.execute(target)

    assert compiled == []
    assert linked == []


def test_task_deduplication():
    compiled_files = []

    def compile(ctx):
        compiled_files.append((ctx.target, ctx.sources))

    tasks = [
        Task(
            matcher=RegularExpressionMatcher(target="b", sources=["a"]), handler=compile
        ),
        Task(
            matcher=RegularExpressionMatcher(target="c", sources=["b"]), handler=compile
        ),
        Task(
            matcher=RegularExpressionMatcher(target="d", sources=["b", "c"]),
            handler=compile,
        ),
    ]

    fs = TestFileSystem({"a": 100})

    executor = Executor(fs, tasks, silent=True)
    executor.execute("d")

    assert sorted(compiled_files) == [("b", ["a"]), ("c", ["b"]), ("d", ["b", "c"])]


def test_run_phony_task():
    run = False

    def execute(ctx):
        nonlocal run
        run = True

    tasks = [
        Task(
            matcher=PlainTextMatcher(target="clean", sources=[]),
            handler=execute,
            phony=True,
        ),
    ]

    fs = TestFileSystem({})

    executor = Executor(fs, tasks, silent=True)
    executor.execute("clean")

    assert run


@pytest.mark.parametrize(
    "fs_config,expected",
    [
        (
            {
                "a.txt": 100,
                "clean": 120,
            },
            False,
        ),
        (
            {
                "a.txt": 130,
                "clean": 120,
            },
            True,
        ),
    ],
)
def test_phony_task_with_recorded_timestamp(fs_config, expected):
    run = False

    def execute(ctx):
        nonlocal run
        run = True

    tasks = [
        Task(
            matcher=PlainTextMatcher(target="clean", sources=["a.txt"]),
            handler=execute,
            phony=True,
        ),
    ]

    fs = TestFileSystem(fs_config)

    executor = Executor(fs, tasks, silent=True)
    executor.execute("clean")

    assert run == expected


def test_error_for_unknown_task():
    fs = TestFileSystem({})
    executor = Executor(fs, [], silent=True)
    with pytest.raises(Exception):
        executor.execute("all")
