"""Test file exclusion in the jacobus API and CLI."""

from __future__ import annotations

__all__: list[str] = ["TestExclude"]

import tempfile
import unittest
from pathlib import Path
from typing import Self

from jacobus import main, parse_args, run


class TestExclude(unittest.TestCase):
    """Test the exclude option introduced in version 2.5."""

    root: Path
    original: bytes = b"\nalpha   \n\n"
    normalized: bytes = b"alpha\n"

    def setUp(self: Self, /) -> None:
        tmp: tempfile.TemporaryDirectory[str]
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def _write(self: Self, /, name: str) -> Path:
        path: Path
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.original)
        return path

    def test_default_excludes_nothing(self: Self, /) -> None:
        a: Path
        b: Path
        a = self._write("a.txt")
        b = self._write("b.txt")

        run(str(self.root / "*.txt"))

        self.assertEqual(a.read_bytes(), self.normalized)
        self.assertEqual(b.read_bytes(), self.normalized)

    def test_empty_exclude_iterable(self: Self, /) -> None:
        a: Path
        a = self._write("a.txt")

        run(str(a), exclude=[])

        self.assertEqual(a.read_bytes(), self.normalized)

    def test_exclude_exact_path(self: Self, /) -> None:
        kept: Path
        skipped: Path
        kept = self._write("keep.txt")
        skipped = self._write("skip.txt")

        run(str(self.root / "*.txt"), exclude=(str(skipped),))

        self.assertEqual(kept.read_bytes(), self.normalized)
        self.assertEqual(skipped.read_bytes(), self.original)

    def test_exclude_overrides_explicit_and_duplicate_inclusions(
        self: Self, /
    ) -> None:
        kept: Path
        skipped: Path
        kept = self._write("keep.txt")
        skipped = self._write("skip.txt")

        run(
            str(skipped),
            str(self.root / "*.txt"),
            str(skipped),
            exclude=(str(skipped),),
        )

        self.assertEqual(kept.read_bytes(), self.normalized)
        self.assertEqual(skipped.read_bytes(), self.original)

    def test_multiple_overlapping_exclude_patterns(self: Self, /) -> None:
        first: Path
        kept: Path
        path: Path
        second: Path
        third: Path
        kept = self._write("keep.txt")
        first = self._write("skip-a.txt")
        second = self._write("skip-b.txt")
        third = self._write("other.txt")

        run(
            str(self.root / "*.txt"),
            exclude=(str(self.root / "skip-*.txt"), str(first), str(third)),
        )

        self.assertEqual(kept.read_bytes(), self.normalized)
        for path in (first, second, third):
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), self.original)

    def test_recursive_directory_exclusion(self: Self, /) -> None:
        first: Path
        kept: Path
        path: Path
        second: Path
        sibling: Path
        kept = self._write("src/nested/keep.py")
        first = self._write("generated/a.py")
        second = self._write("generated/nested/b.py")
        sibling = self._write("generated-other/c.py")

        run(
            str(self.root / "**" / "*.py"),
            exclude=(str(self.root / "generated" / "**"),),
        )

        for path in (kept, sibling):
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), self.normalized)
        for path in (first, second):
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), self.original)

    def test_directory_name_alone_does_not_exclude_contents(
        self: Self, /
    ) -> None:
        path: Path
        path = self._write("generated/nested/a.py")

        run(
            str(self.root / "**" / "*.py"),
            exclude=(str(self.root / "generated"),),
        )

        self.assertEqual(path.read_bytes(), self.normalized)

    def test_recursive_basename_exclusion(self: Self, /) -> None:
        first: Path
        kept: Path
        second: Path
        first = self._write("setup.py")
        second = self._write("nested/deep/setup.py")
        kept = self._write("nested/deep/module.py")

        run(
            str(self.root / "**" / "*.py"),
            exclude=(str(self.root / "**" / "setup.py"),),
        )

        self.assertEqual(first.read_bytes(), self.original)
        self.assertEqual(second.read_bytes(), self.original)
        self.assertEqual(kept.read_bytes(), self.normalized)

    def test_unmatched_and_outside_inclusion_exclusions(self: Self, /) -> None:
        kept: Path
        outside: Path
        kept = self._write("keep.txt")
        outside = self._write("outside.py")

        run(
            str(self.root / "*.txt"),
            exclude=(str(self.root / "missing*"), str(outside)),
        )

        self.assertEqual(kept.read_bytes(), self.normalized)
        self.assertEqual(outside.read_bytes(), self.original)

    def test_exclude_all_matches(self: Self, /) -> None:
        a: Path
        b: Path
        pattern: str
        a = self._write("a.txt")
        b = self._write("b.txt")
        pattern = str(self.root / "*.txt")

        run(pattern, exclude=(pattern,))

        self.assertEqual(a.read_bytes(), self.original)
        self.assertEqual(b.read_bytes(), self.original)

    def test_exclude_accepts_generator(self: Self, /) -> None:
        first: Path
        kept: Path
        second: Path
        kept = self._write("keep.txt")
        first = self._write("a.txt")
        second = self._write("b.txt")

        run(
            str(self.root / "*.txt"),
            exclude=(str(path) for path in (first, second)),
        )

        self.assertEqual(kept.read_bytes(), self.normalized)
        self.assertEqual(first.read_bytes(), self.original)
        self.assertEqual(second.read_bytes(), self.original)

    def test_excluded_invalid_utf8_is_not_read(self: Self, /) -> None:
        invalid: bytes
        kept: Path
        skipped: Path
        kept = self._write("keep.txt")
        skipped = self.root / "skip.txt"
        invalid = b"\xff\xfe\x00"
        skipped.write_bytes(invalid)

        run(str(self.root / "*.txt"), exclude=(str(skipped),))

        self.assertEqual(kept.read_bytes(), self.normalized)
        self.assertEqual(skipped.read_bytes(), invalid)

    def test_cli_exclude_defaults_to_empty(self: Self, /) -> None:
        self.assertEqual(parse_args([]).exclude, [])

    def test_cli_repeated_exclude_options(self: Self, /) -> None:
        args: list[str]
        exclusions: list[str]
        first: Path
        kept: Path
        pattern: str
        second: Path
        kept = self._write("src/keep.py")
        first = self._write("generated/nested/a.py")
        second = self._write("src/setup.py")
        pattern = str(self.root / "**" / "*.py")
        exclusions = [
            str(self.root / "generated" / "**"),
            str(self.root / "**" / "setup.py"),
        ]
        args = [
            pattern,
            str(second),
            "--exclude",
            exclusions[0],
            "--exclude",
            exclusions[1],
        ]

        self.assertEqual(parse_args(args).exclude, exclusions)
        self.assertEqual(main(args), 0)

        self.assertEqual(kept.read_bytes(), self.normalized)
        self.assertEqual(first.read_bytes(), self.original)
        self.assertEqual(second.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
