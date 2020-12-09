import re

from .task import Context
from .util import escape_format_str


def process_sources(target, sources, args):
    result = []

    for source in sources:
        if source is None:
            continue
        elif isinstance(source, str):
            result.append(source.format(*args))
        elif callable(source):
            generated = source(target, args)
            if generated:
                result.extend(generated)
        else:
            raise Exception("Unknown source:", source)

    return result


def escape_sources(sources, f):
    return [source if callable(source) else f(source) for source in sources]


def escape_target(target, f):
    if callable(target):
        return target
    else:
        return f(target)


class RegularExpressionMatcher:
    def __init__(self, target, sources):
        self.target_re = re.compile(target)
        self.sources = sources

    def match(self, target):
        m = self.target_re.fullmatch(target)
        if m:
            sources = process_sources(target, self.sources, m.groups())
            return Context(target=target, sources=sources)


class PercentPatternMatcher(RegularExpressionMatcher):
    def __init__(self, target, sources):
        super().__init__(
            escape_target(target, self.translate_target),
            escape_sources(sources, lambda s: escape_format_str(s).replace("%", "{}")),
        )

    @staticmethod
    def translate_target(target):
        # In some Python versions, re.escape will convert `%` into `\%`,
        # while in other version, '%' will be kept unchanged
        return re.escape(target).replace("\\%", "(.*?)").replace("%", "(.*?)")


class PlainTextMatcher(RegularExpressionMatcher):
    def __init__(self, target, sources):
        super().__init__(
            escape_target(target, lambda t: re.escape(t)),
            escape_sources(sources, escape_format_str),
        )
