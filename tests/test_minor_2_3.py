"""Test the jacobus whitespace normalization tool comprehensively."""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import sys
import tempfile
import typing
import unittest
from typing import Self
from unittest.mock import patch

from jacobus import main, run

__all__ = ["TestJacobus"]


class TestJacobus(unittest.TestCase):
    """TestCase for jacobus public interface."""

    maxDiff: int | None

    def setUp(self: Self) -> None:
        self.maxDiff = None

    def _write_text_file(
        self: Self, base: pathlib.Path, name: str, content: str
    ) -> pathlib.Path:
        """Write text content to a file in base directory. Return the path."""
        p: pathlib.Path
        p = base / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def _read_lines(self: Self, path: pathlib.Path) -> list[str]:
        """Read file and return lines with keepends=True."""
        text: str
        text = path.read_text(encoding="utf-8")
        return text.splitlines(keepends=True)

    def test_run_no_patterns(self: Self) -> None:
        """Run with no file patterns does nothing and succeeds."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            # create a file but don't pass pattern
            f: pathlib.Path = self._write_text_file(
                tmpdir, "test.txt", "hello\nworld\n"
            )
            original: list[str] = self._read_lines(f)
            run()  # no patterns
            self.assertListEqual(self._read_lines(f), original)

    def test_run_non_matching_pattern(self: Self) -> None:
        """Non-matching glob pattern is ignored, no error."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            f: pathlib.Path = self._write_text_file(
                tmpdir, "test.txt", "hello\n"
            )
            run(str(tmpdir / "*.nonexistent"))
            self.assertListEqual(self._read_lines(f), ["hello\n"])

    def test_run_basic_rstrip_vstrip(self: Self) -> None:
        """Basic run rstrips lines and vstrips leading/trailing blanks."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "  hello  \n\n\n  world  \n\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "a.txt", content)
            run(str(f))
            lines: list[str] = self._read_lines(f)
            # rstrip keeps leading ws; vstrip removed trailing blank line
            self.assertListEqual(lines, ["  hello\n", "\n", "\n", "  world\n"])

    def test_run_empty_0_removes_all_blanks(self: Self) -> None:
        """--empty 0 removes all blank lines (after vstrip)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "a\n\n\nb\n\nc\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "b.txt", content)
            run(str(f), empty=0)
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["a\n", "b\n", "c\n"])

    def test_run_empty_1_keeps_single_blanks(self: Self) -> None:
        """--empty 1 collapses multiple blanks to single."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "a\n\n\n\nb\n\nc\n\n\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "c.txt", content)
            run(str(f), empty=1)
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["a\n", "\n", "b\n", "\n", "c\n"])

    def test_run_empty_none_keeps_internal_blanks(self: Self) -> None:
        """Default (empty=None) keeps internal blanks after vstrip."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "\n\nx\n\n\ny\n\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "d.txt", content)
            run(str(f))  # empty=None
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["x\n", "\n", "\n", "y\n"])

    def test_run_sort_removes_blanks_via_vstrip(self: Self) -> None:
        """--sort sorts lines and vstrip removes leading blanks."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "c\n\na\nb\n\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "e.txt", content)
            run(str(f), sort=True)
            lines: list[str] = self._read_lines(f)
            # after sort: blanks to front; vstrip removes them
            self.assertListEqual(lines, ["a\n", "b\n", "c\n"])

    def test_run_unique_removes_dups(self: Self) -> None:
        """--unique removes duplicate lines (arbitrary order from set)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "a\nb\na\nb\nc\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "f.txt", content)
            run(str(f), unique=True)
            lines: list[str] = self._read_lines(f)
            # dups removed; no blanks so vstrip irrelevant; order arbitrary
            processed_set: set[str] = set(lines)
            self.assertEqual(len(lines), len(processed_set))
            self.assertSetEqual(processed_set, {"a\n", "b\n", "c\n"})

    def test_run_sort_and_unique(self: Self) -> None:
        """--sort --unique gives sorted unique lines, blanks removed."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "c\nb\na\nb\n\nc\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "g.txt", content)
            run(str(f), sort=True, unique=True)
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["a\n", "b\n", "c\n"])

    def test_run_indent_scales(self: Self) -> None:
        """--indent changes indent width by gcd scaling."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "  def f():\n    print(1)\n      x\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "h.py", content)
            run(str(f), indent=4)
            lines: list[str] = self._read_lines(f)
            # divisor=2; each indent level scaled: new = (old_diff//2) * 4
            self.assertListEqual(
                lines,
                ["    def f():\n", "        print(1)\n", "            x\n"],
            )

    def test_run_indent_no_change_if_zero_divisor(self: Self) -> None:
        """If no common indent (divisor=0), indent option does nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "def f():\nprint(1)\n"  # all diff=0 so divisor=0
            f: pathlib.Path = self._write_text_file(tmpdir, "i.py", content)
            run(str(f), indent=4)
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["def f():\n", "print(1)\n"])

    def test_run_indent_dedent_to_zero(self: Self) -> None:
        """--indent 0 removes all leading spaces."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "    indented\n        more\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "j.py", content)
            run(str(f), indent=0)
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["indented\n", "more\n"])

    def test_run_combination_indent_sort_empty(self: Self) -> None:
        """Test combined options: indent, unique+sort, empty in run order."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "  b\n\n  a\n  b\n    c\n"
            f: pathlib.Path = self._write_text_file(tmpdir, "k.py", content)
            run(str(f), indent=2, sort=True, unique=True, empty=0)
            lines: list[str] = self._read_lines(f)
            # after unique+sort+vstrip: "    c\n" sorts before "  a\n"
            self.assertListEqual(lines, ["    c\n", "  a\n", "  b\n"])

    def test_run_multiple_files_and_glob(self: Self) -> None:
        """Multiple patterns and globs process each file once."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            f1: pathlib.Path = self._write_text_file(
                tmpdir, "m1.txt", "z\ny\n"
            )
            f2: pathlib.Path = self._write_text_file(tmpdir, "m2.txt", "x\n")
            sub: pathlib.Path = tmpdir / "sub"
            f3: pathlib.Path = self._write_text_file(sub, "m3.txt", "w\n")
            # glob non-recursive misses sub, ** works with recursive
            run(str(tmpdir / "m*.txt"), str(tmpdir / "**/m3.txt"), sort=True)
            self.assertListEqual(self._read_lines(f1), ["y\n", "z\n"])
            self.assertListEqual(self._read_lines(f2), ["x\n"])
            self.assertListEqual(self._read_lines(f3), ["w\n"])

    def test_run_dedups_absfiles(self: Self) -> None:
        """Same file matched by multiple patterns processed only once."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            f: pathlib.Path = self._write_text_file(
                tmpdir, "n.txt", "line1\nline1\n"
            )
            run(str(f), str(f), unique=True)
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["line1\n"])  # unique removed dup

    def test_run_skips_directories(self: Self) -> None:
        """Directory paths are skipped even if pattern matches."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            (tmpdir / "dir").mkdir()
            f: pathlib.Path = self._write_text_file(
                tmpdir, "o.txt", "content\n"
            )
            run(str(tmpdir / "*"))  # matches dir and o.txt
            self.assertListEqual(self._read_lines(f), ["content\n"])

    def test_main_calls_run_equivalent(self: Self) -> None:
        """main(args) equivalent to run for file processing."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            f: pathlib.Path = self._write_text_file(tmpdir, "p.txt", "B\nA\n")
            with patch("importlib.metadata.version"):
                main(["--sort", str(f)])
            lines: list[str] = self._read_lines(f)
            self.assertListEqual(lines, ["A\n", "B\n"])

    def test_main_version(self: Self) -> None:
        """--version prints version and exits 0."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.return_value = "0.1.0"
            stdout: io.StringIO
            with self.assertRaises(SystemExit) as cm:
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    main(["--version"])
            self.assertEqual(cm.exception.code, 0)
            output: str = stdout.getvalue()
            self.assertIn("0.1.0", output)

    def test_main_help(self: Self) -> None:
        """--help prints usage and exits 0."""
        stdout: io.StringIO
        with patch("importlib.metadata.version"):
            with self.assertRaises(SystemExit) as cm:
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        output: str = stdout.getvalue()
        self.assertIn("usage:", output.lower())
        self.assertIn("normalizes whitespace", output)

    def test_run_empty_file(self: Self) -> None:
        """Empty file stays empty."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            f: pathlib.Path = self._write_text_file(tmpdir, "empty.txt", "")
            run(str(f), sort=True, unique=True, empty=0, indent=4)
            self.assertEqual(f.read_text(encoding="utf-8"), "")

    def test_run_only_blanks(self: Self) -> None:
        """Only-blank file becomes empty after vstrip."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            f: pathlib.Path
            f = self._write_text_file(tmpdir, "blanks.txt", "\n\n\n")
            run(str(f))
            self.assertEqual(f.read_text(encoding="utf-8"), "")

    def test_run_preserves_final_newline(self: Self) -> None:
        """Processed non-empty file ends with exactly one newline."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            content: str = "last line without nl"
            f: pathlib.Path
            f = self._write_text_file(tmpdir, "final.txt", content)
            run(str(f))
            text: str = f.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertNotIn("\n\n", text)  # no extra

    def test_run_with_at_file(self: Self) -> None:
        """fromfile_prefix @ allows args from file (argparse feature)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir: pathlib.Path = pathlib.Path(tmp)
            argsfile: pathlib.Path = self._write_text_file(
                tmpdir, "args.txt", "--sort\n--unique\n"
            )
            datafile: pathlib.Path = self._write_text_file(
                tmpdir, "data.txt", "z\nz\na\n"
            )
            # main with @file
            with patch("importlib.metadata.version"):
                main([f"@{argsfile}", str(datafile)])
            lines: list[str] = self._read_lines(datafile)
            self.assertListEqual(lines, ["a\n", "z\n"])


if __name__ == "__main__":
    unittest.main()
