from make_py.matcher import (
    RegularExpressionMatcher,
    PercentPatternMatcher,
    PlainTextMatcher,
)


def test_regex_matcher():
    matcher = RegularExpressionMatcher(
        target=r"([^-]+)-([^\.]+)\.txt", sources=["{0}.txt", "{1}.txt"]
    )

    ctx = matcher.match("foo-bar.txt")
    assert ctx is not None
    assert ctx.target == "foo-bar.txt"
    assert ctx.sources == ["foo.txt", "bar.txt"]


def test_percent_matcher():
    matcher = PercentPatternMatcher(target="build/%.o", sources=["%.c", "include/%.h"])

    ctx = matcher.match("build/test.o")
    assert ctx is not None
    assert ctx.target == "build/test.o"
    assert ctx.sources == ["test.c", "include/test.h"]


def test_plain_text_matcher():
    matcher = PlainTextMatcher(target="{filename.#-+}", sources=["{}{}"])

    ctx = matcher.match("{filename.#-+}")
    assert ctx is not None
    assert ctx.target == "{filename.#-+}"
    assert ctx.sources == ["{}{}"]
