# make.py

[![PyPI version](https://badge.fury.io/py/make-py.svg)](https://badge.fury.io/py/make-py)

`make.py` is like `make` but with its build configuration written in Python.

## Example

For the following `Makefile`:

```makefile
CC=gcc
OUTPUT=build

all: $(OUTPUT)/main

$(OUTPUT)/%.o: %.c
	mkdir -p $(dir $@)
	$(CC) -MMD -c $< -o $@

$(OUTPUT)/main: $(OUTPUT)/hello.o $(OUTPUT)/main.o
	$(CC) $^ -o $@

clean:
	rm -rf $(OUTPUT)

.PHONY: clean

-include $(OUTPUT)/*.d
```

The equivalent `Makefile.py` is:

```python
from pathlib import Path
from shutil import rmtree
from subprocess import check_call

from make_py import task, rule, phony_task

CC = "gcc"
OUTPUT = "build"

phony_task("all", f"{OUTPUT}/main")


def collect_c_dependencies(target, target_regex_groups):
    dep_file = Path(target).with_suffix(".d")
    if dep_file.exists():
        return dep_file.read_text().split(":")[1].strip().split(" ")


# missing parent directories will be made automatically
@rule(f"{OUTPUT}/%.o", ["%.c", collect_c_dependencies])
def compile_c(ctx):
    check_call([CC, "-MMD", "-c", ctx.source, "-o", ctx.target])


@rule(f"{OUTPUT}/main", [f"{OUTPUT}/{o}" for o in ["hello.o", "main.o"]])
def link(ctx):
    check_call([CC, *ctx.sources, "-o", ctx.target])


@task()
def clean(ctx):
    rmtree(OUTPUT, ignore_errors=True)
```

The commands can be executed by `make.py` the same way as executing `make`

For more examples, refer to the `examples` folder in project root.
