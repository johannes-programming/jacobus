import argparse
import io
import pathlib
import typing
from collections.abc import Iterable
from importlib import metadata
from typing import Optional

from jacobus.const.Const import Const

__all__ = ["main", "run"]


def main(args: typing.Optional[list[str]] = None, /) -> None:
    parser: argparse.ArgumentParser
    space: argparse.Namespace
    parser = argparse.ArgumentParser(
        description=Const.const.varia.get("description"),
        formatter_class=argparse.RawTextHelpFormatter,
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        dest="version",
        version=metadata.version("jacobus"),
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        dest="files",
    )
    parser.add_argument(
        "--indent",
        type=int,
    )
    parser.add_argument(
        "root",
    )
    space = parser.parse_args(args)
    # kwargs = vars(space)
    run(
        space.root,
        files=space.files,
        indent=space.indent,
    )


def run(
    root: str,
    /,
    *,
    files: Iterable[str] = (),
    indent: Optional[int] = None,
) -> None:
    diff: int
    divisor: int
    index: int
    line: str
    lines: list[str]
    path: pathlib.Path
    paths: list[pathlib.Path]
    stream: io.TextIOWrapper
    paths = list()
    for file in files:
        for path in pathlib.Path(root).glob(file):
            if path.is_file() and path not in paths:
                paths.append(path)
    for path in paths:
        with open(file=path, mode="r") as stream:
            lines = stream.readlines()
        for index in range(len(lines)):
            lines[index] = lines[index].rstrip() + "\n"
        while len(lines) and lines[0] == "\n":
            lines.pop(0)
        while len(lines) and lines[-1] == "\n":
            lines.pop()
            continue
        divisor = 0
        if indent is not None:
            for line in lines:
                diff = len(line) - len(line.lstrip(" "))
                divisor = gcd(divisor, diff)
            for index in range(len(lines) * bool(divisor)):
                diff = len(lines[index]) - len(lines[index].lstrip(" "))
                diff //= divisor
                diff *= indent
                lines[index] = (" " * diff) + lines[index].lstrip(" ")
        with open(file=path, mode="w") as stream:
            stream.writelines(lines)


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a
