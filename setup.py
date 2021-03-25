from pathlib import Path

import setuptools

HERE = Path(__file__).parent

long_description = (HERE / "README.md").read_text()

setuptools.setup(
    name="make_py",
    version="0.1.1",
    author="Yifei Wang",
    author_email="yifei529@gmail.com",
    description="A make equivalent in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cww0614/make.py",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ["make.py=make_py.__main__:main"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
