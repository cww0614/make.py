from .matcher import RegularExpressionMatcher, PercentPatternMatcher, PlainTextMatcher
from .task import TASKS, Task
from .util import to_list


def rule(target, sources, regex=False, phony=False):
    sources = to_list(sources)

    def wrap(func):
        if regex:
            matcher = RegularExpressionMatcher
        elif target.find("%") >= 0:
            matcher = PercentPatternMatcher
        else:
            matcher = PlainTextMatcher

        TASKS.append(
            Task(
                matcher=matcher(sources=sources, target=target),
                handler=func,
                phony=phony,
            )
        )

        return func

    return wrap


def task(sources=None, name=None):
    if sources is None:
        sources = []

    def wrap(func):
        if not name:
            target = func.__name__
        else:
            target = name

        return rule(target, sources, phony=True)(func)

    return wrap


def phony_task(name, sources=None):
    task(sources, name=name)(lambda _: None)
