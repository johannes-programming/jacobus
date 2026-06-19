import argparse
import glob
import io
import os
import typing
from collections.abc import Iterable
from importlib import metadata
from typing import Optional

__all__ = ["main", "run"]


def gcd(a: int, b: int, /) -> int:
    while b:
        a, b = b, a % b
    return a


def go_empty(*lines_: str, empty: Optional[int]) -> list[str]:
    ans: list[str]
    count: int
    line: str
    if empty is None:
        return list(lines_)
    ans = []
    count = 0
    for line in lines_:
        if line == "\n":
            count += 1
        else:
            count = 0
        if count <= empty:
            ans.append(line)
    return ans


def go_indent(*lines_: str, indent: Optional[int]) -> list[str]:
    diff: int
    divisor: int
    line: str
    lines: list[str]
    lines = list(lines_)
    if indent is None:
        return lines
    divisor = 0
    for line in lines:
        diff = len(line) - len(line.lstrip(" "))
        divisor = gcd(divisor, diff)
    for index in range(len(lines) * bool(divisor)):
        diff = len(lines[index]) - len(lines[index].lstrip(" "))
        diff //= divisor
        diff *= indent
        lines[index] = (" " * diff) + lines[index].lstrip(" ")
    return lines


def go_rstrip(*lines_: str) -> list[str]:
    index: int
    lines: list[str]
    lines = list(lines_)
    for index in range(len(lines)):
        lines[index] = lines[index].rstrip() + "\n"
    return lines


def go_sort(*lines_: str, sort: bool) -> list[str]:
    if sort:
        return list(sorted(lines_))
    else:
        return list(lines_)


def go_vstrip(*lines_: str) -> list[str]:
    lines: list[str]
    lines = list(lines_)
    while len(lines) and lines[0] == "\n":
        lines.pop(0)
    while len(lines) and lines[-1] == "\n":
        lines.pop()
        continue
    return lines


def main(args: typing.Optional[list[str]] = None, /) -> None:
    parser: argparse.ArgumentParser
    space: argparse.Namespace
    parser = argparse.ArgumentParser(
        description="This project normalizes whitespace.",
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
        "--empty",
        help="This option limits the number of consecutive empty lines.",
        type=int,
    )
    parser.add_argument(
        "--indent",
        help="This option alters the indentation.",
        type=int,
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        help="This flag sorts the lines.",
    )
    parser.add_argument(
        "filepatterns",
        default=[],
        help="These arguments give the patterns of the file.",
        nargs="*",
    )
    kwargs = vars(parser.parse_args(args))
    run(*kwargs.pop("filepatterns"), **kwargs)


def run(
    *filepatterns: str,
    empty: Optional[int] = None,
    indent: Optional[int] = None,
    sort: bool = False,
) -> None:
    absfile: str
    absfiles: list[str]
    lines: list[str]
    pattern: str
    stream: io.TextIOWrapper
    absfiles = list()
    for pattern in filepatterns:
        for absfile in map(
            os.path.abspath, glob.iglob(pattern, recursive=True)
        ):
            if absfile in absfiles:
                continue
            if os.path.isfile(absfile):
                absfiles.append(absfile)
    for absfile in absfiles:
        with open(file=absfile, mode="r") as stream:
            lines = stream.readlines()
        lines = go_rstrip(*lines)
        lines = go_sort(*lines, sort=sort)
        lines = go_vstrip(*lines)
        lines = go_empty(*lines, empty=empty)
        lines = go_indent(*lines, indent=indent)
        with open(file=absfile, mode="w") as stream:
            stream.writelines(lines)
