from make_py import rule, task
from pathlib import Path


@rule(r"example[^-]+\.txt", [], regex=True)
def generate_example(ctx):
    with open(ctx.target, "w") as t:
        t.write(ctx.target + "\n")


# `{0}`, `{1}`, ... refers to the first, # second, ... group in
# regular expression
@rule(r"([^\-]+)-([^\.]+)\.txt", ["{0}.txt", "{1}.txt"], regex=True)
def concat(ctx):
    with open(ctx.target, "w") as t:
        for path in ctx.sources:
            with open(path) as s:
                t.write(s.read())


@task()
def clean(ctx):
    for p in Path(".").glob("*.txt"):
        p.unlink()
