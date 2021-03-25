from glob import glob
from sys import executable
from subprocess import check_call
from shutil import rmtree

from make_py import task


@task()
def install_release_deps(ctx):
    check_call(
        [
            executable,
            "-m",
            "pip",
            "install",
            "--user",
            "--upgrade",
            "setuptools",
            "wheel",
            "twine",
        ]
    )


@task()
def release(ctx):
    rmtree("dist")
    check_call([executable, "setup.py", "sdist", "bdist_wheel"])
    check_call([executable, "-m", "twine", "upload", *glob("dist/*")])
