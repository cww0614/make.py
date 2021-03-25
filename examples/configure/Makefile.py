from shutil import which

from make_py import phony_task, task, PersistentVariables

VARIABLES = PersistentVariables("variables.json")
CC = VARIABLES["CC"]

phony_task("all", "print")


@task()
def configure(ctx):
    CC.set(which("gcc"))


@task()
def print_variables(ctx):
    print("CC =", CC.get())


@task()
def clean(ctx):
    # If the variable collection isn't empty, it will be created again
    # when the script exits
    VARIABLES.clear()
    if VARIABLES.path.exists():
        VARIABLES.path.unlink()
