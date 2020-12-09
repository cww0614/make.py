from time import sleep

import pytest

from make_py.executor import Executor, JobPool
from make_py.matcher import (
    RegularExpressionMatcher,
    PlainTextMatcher,
    PercentPatternMatcher,
)
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


def create_test_executor(fs, tasks, jobs=1):
    return Executor(fs, JobPool(), tasks, silent=True, jobs=jobs)


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

    executor = create_test_executor(fs, tasks)
    executor.execute("test.o")

    assert compiled == [("test.o", ["test.c"])]
    assert linked == []


def test_dont_recompile():
    fs = TestFileSystem({"test.c": 100, "test.o": 110})
    tasks, compiled, linked = fake_compile_tasks()

    executor = create_test_executor(fs, tasks)
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

    executor = create_test_executor(fs, tasks)
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

    executor = create_test_executor(fs, tasks)
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

    executor = create_test_executor(fs, tasks)
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

    executor = create_test_executor(fs, tasks)
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

    executor = create_test_executor(fs, tasks)
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

    executor = create_test_executor(fs, tasks)
    executor.execute("clean")

    assert run == expected


def test_error_for_unknown_task():
    fs = TestFileSystem({})
    executor = create_test_executor(fs, [])
    with pytest.raises(Exception):
        executor.execute("all")


def test_parallelization():
    task1_running = False
    task2_running = False

    def task1(ctx):
        nonlocal task1_running, task2_running
        task1_running = True
        while not task2_running:
            sleep(0.1)

    def task2(ctx):
        nonlocal task1_running, task2_running
        task2_running = True
        while not task2_running:
            sleep(0.1)

    tasks = [
        Task(
            matcher=PlainTextMatcher(target="task1", sources=[]),
            handler=task1,
            phony=True,
        ),
        Task(
            matcher=PlainTextMatcher(target="task2", sources=[]),
            handler=task2,
            phony=True,
        ),
        Task(
            matcher=PlainTextMatcher(target="all", sources=["task1", "task2"]),
            handler=lambda _: None,
            phony=True,
        ),
    ]

    fs = TestFileSystem({})

    executor = create_test_executor(fs, tasks, jobs=2)
    executor.execute("all")


def test_order():
    finished = False
    link_after_compile_finished = False

    def compile(ctx):
        nonlocal finished
        sleep(1)
        finished = True

    def link(ctx):
        nonlocal link_after_compile_finished
        link_after_compile_finished = finished

    tasks = [
        Task(
            matcher=PlainTextMatcher(target="compile", sources=[]),
            handler=compile,
            phony=True,
        ),
        Task(
            matcher=PlainTextMatcher(target="link", sources=["compile"]),
            handler=link,
            phony=True,
        ),
    ]

    fs = TestFileSystem({})

    executor = create_test_executor(fs, tasks, jobs=4)
    executor.execute("link")

    assert link_after_compile_finished


def test_failure_task():
    task1_executed = 0
    task2_executed = 0

    def task1(ctx):
        nonlocal task1_executed
        sleep(1)
        task1_executed += 1

    def task2(ctx):
        nonlocal task2_executed
        task2_executed += 1
        raise Exception("Exception on purpose")

    tasks = [
        Task(
            matcher=PercentPatternMatcher(target="task1%", sources=[]),
            handler=task1,
            phony=True,
        ),
        Task(
            matcher=PercentPatternMatcher(target="task2%", sources=[]),
            handler=task2,
            phony=True,
        ),
        Task(
            matcher=PlainTextMatcher(
                target="all",
                sources=[
                    "task1_1",
                    "task2_1",
                    "task1_2",
                    "task2_2",
                    "task1_3",
                    "task2_3",
                ],
            ),
            handler=lambda _: None,
            phony=True,
        ),
    ]

    fs = TestFileSystem({})
    executor = create_test_executor(fs, tasks, jobs=2)
    executor.execute("all")

    assert task1_executed == 1
    assert task2_executed == 1
