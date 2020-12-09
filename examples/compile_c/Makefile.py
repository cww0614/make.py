from pathlib import Path
from shutil import rmtree
from subprocess import check_call

from make_py import task, rule, phony_task

CC = "gcc"
OUTPUT = "build"

phony_task("all", f"{OUTPUT}/main")


# Collect dependencies from .d files generated using `-MMD` option
def collect_c_dependencies(target, args):
    dep_file = Path(target).with_suffix(".d")
    if dep_file.exists():
        return dep_file.read_text().split(":")[1].strip().split(" ")


# Parent directories will be created automatically
@rule(f"{OUTPUT}/%.o", ["%.c", collect_c_dependencies])
def compile_c(ctx):
    check_call([CC, "-MMD", "-c", ctx.source, "-o", ctx.target])


@rule(f"{OUTPUT}/main", [f"{OUTPUT}/{o}" for o in ["hello.o", "main.o"]])
def link(ctx):
    check_call([CC, *ctx.sources, "-o", ctx.target])


@task()
def clean(ctx):
    rmtree(OUTPUT, ignore_errors=True)
