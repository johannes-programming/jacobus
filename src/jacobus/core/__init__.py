from __future__ import annotations

__all__: list[str] = ["main", "run"]

import argparse
import glob
import io
import os
from collections import abc
from importlib import metadata


def gcd(a: int, b: int, /) -> int:
    while b:
        a, b = b, a % b
    return a


def go_empty(*lines: str, empty: int | None) -> list[str]:
    ans: list[str]
    count: int
    line: str
    if empty is None:
        return list(lines)
    ans = []
    count = 0
    for line in lines:
        if line == "\n":
            count += 1
        else:
            count = 0
        if count <= empty:
            ans.append(line)
    return ans


def go_indent(*lines_: str, indent: int | None) -> list[str]:
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


def go_rstrip(*lines: str) -> list[str]:
    index: int
    lines_: list[str]
    lines_ = list(lines)
    for index in range(len(lines_)):
        lines_[index] = lines_[index].rstrip() + "\n"
    return lines_


def go_sort(*lines: str, sort: bool) -> list[str]:
    if sort:
        return list(sorted(lines))
    else:
        return list(lines)


def go_unique(*lines: str, unique: bool) -> list[str]:
    if unique:
        return list(set(lines))
    else:
        return list(lines)


def go_vstrip(*lines: str) -> list[str]:
    lines_: list[str]
    lines_ = list(lines)
    while len(lines_) and lines_[0] == "\n":
        lines_.pop(0)
    while len(lines_) and lines_[-1] == "\n":
        lines_.pop()
        continue
    return lines_


def main(args: abc.Iterable[str] | None = None, /) -> None:
    parser: argparse.ArgumentParser
    version: str
    parser = argparse.ArgumentParser(
        description="This project normalizes whitespace.",
        fromfile_prefix_chars="@",
        prog="jacobus",
    )
    version = "%(prog)s, " + metadata.version("jacobus")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        dest="version",
        version=version,
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
        "--unique",
        action="store_true",
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
    empty: int | None = None,
    indent: int | None = None,
    sort: bool = False,
    unique: bool = False,
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
        lines = go_indent(*lines, indent=indent)
        lines = go_unique(*lines, unique=unique)
        lines = go_sort(*lines, sort=sort)
        lines = go_vstrip(*lines)
        lines = go_empty(*lines, empty=empty)
        with open(file=absfile, mode="w") as stream:
            stream.writelines(lines)
