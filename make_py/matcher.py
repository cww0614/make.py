import re

from .task import Context
from .util import escape_format_str


class RegularExpressionMatcher:
    def __init__(self, target, sources):
        self.target_re = re.compile(target)
        self.sources = sources

    def match(self, target):
        m = self.target_re.fullmatch(target)
        if m:
            sources = [s.format(*m.groups()) for s in self.sources]
            return Context(target=target, sources=sources)


class PercentPatternMatcher(RegularExpressionMatcher):
    def __init__(self, target, sources):
        super().__init__(
            re.escape(target).replace("%", "(.*?)"),
            [escape_format_str(s).replace("%", "{}") for s in sources],
        )


class PlainTextMatcher(RegularExpressionMatcher):
    def __init__(self, target, sources):
        super().__init__(re.escape(target), [escape_format_str(s) for s in sources])
