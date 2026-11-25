"""Test the jacobus whitespace normalization tool comprehensively."""

from __future__ import annotations

__all__: list[str] = ["TestJacobus"]

import io
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from typing import Self
from unittest.mock import MagicMock, patch

from jacobus import main, run


class TestJacobus(unittest.TestCase):
    """TestCase for jacobus public interface."""

    maxDiff: int | None

    def setUp(self: Self, /) -> None:
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

    def test_run_no_patterns(self: Self, /) -> None:
        """Run with no file patterns does nothing and succeeds."""
        f: pathlib.Path
        original: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            # create a file but don't pass pattern
            f = self._write_text_file(tmpdir, "test.txt", "hello\nworld\n")
            original = self._read_lines(f)
            run()  # no patterns
            self.assertListEqual(self._read_lines(f), original)

    def test_run_non_matching_pattern(self: Self, /) -> None:
        """Non-matching glob pattern is ignored, no error."""
        f: pathlib.Path
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            f = self._write_text_file(tmpdir, "test.txt", "hello\n")
            run(str(tmpdir / "*.nonexistent"))
            self.assertListEqual(self._read_lines(f), ["hello\n"])

    def test_run_basic_rstrip_vstrip(self: Self, /) -> None:
        """Basic run rstrips lines and vstrips leading/trailing blanks."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "  hello  \n\n\n  world  \n\n"
            f = self._write_text_file(tmpdir, "a.txt", content)
            run(str(f))
            lines = self._read_lines(f)
            # rstrip keeps leading ws; vstrip removed trailing blank line
            self.assertListEqual(lines, ["  hello\n", "\n", "\n", "  world\n"])

    def test_run_empty_0_removes_all_blanks(self: Self, /) -> None:
        """--empty 0 removes all blank lines (after vstrip)."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "a\n\n\nb\n\nc\n"
            f = self._write_text_file(tmpdir, "b.txt", content)
            run(str(f), empty=0)
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["a\n", "b\n", "c\n"])

    def test_run_empty_1_keeps_single_blanks(self: Self, /) -> None:
        """--empty 1 collapses multiple blanks to single."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "a\n\n\n\nb\n\nc\n\n\n"
            f = self._write_text_file(tmpdir, "c.txt", content)
            run(str(f), empty=1)
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["a\n", "\n", "b\n", "\n", "c\n"])

    def test_run_empty_none_keeps_internal_blanks(self: Self, /) -> None:
        """Default (empty=None) keeps internal blanks after vstrip."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "\n\nx\n\n\ny\n\n"
            f = self._write_text_file(tmpdir, "d.txt", content)
            run(str(f))  # empty=None
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["x\n", "\n", "\n", "y\n"])

    def test_run_sort_removes_blanks_via_vstrip(self: Self, /) -> None:
        """--sort sorts lines and vstrip removes leading blanks."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "c\n\na\nb\n\n"
            f = self._write_text_file(tmpdir, "e.txt", content)
            run(str(f), sort=True)
            lines = self._read_lines(f)
            # after sort: blanks to front; vstrip removes them
            self.assertListEqual(lines, ["a\n", "b\n", "c\n"])

    def test_run_unique_removes_dups(self: Self, /) -> None:
        """--unique removes duplicate lines (arbitrary order from set)."""
        content: str
        f: pathlib.Path
        lines: list[str]
        processed_set: set[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "a\nb\na\nb\nc\n"
            f = self._write_text_file(tmpdir, "f.txt", content)
            run(str(f), unique=True)
            lines = self._read_lines(f)
            # dups removed; no blanks so vstrip irrelevant; order arbitrary
            processed_set = set(lines)
            self.assertEqual(len(lines), len(processed_set))
            self.assertSetEqual(processed_set, {"a\n", "b\n", "c\n"})

    def test_run_sort_and_unique(self: Self, /) -> None:
        """--sort --unique gives sorted unique lines, blanks removed."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "c\nb\na\nb\n\nc\n"
            f = self._write_text_file(tmpdir, "g.txt", content)
            run(str(f), sort=True, unique=True)
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["a\n", "b\n", "c\n"])

    def test_run_indent_scales(self: Self, /) -> None:
        """--indent changes indent width by gcd scaling."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "  def f():\n    print(1)\n      x\n"
            f = self._write_text_file(tmpdir, "h.py", content)
            run(str(f), indent=4)
            lines = self._read_lines(f)
            # divisor=2; each indent level scaled: new = (old_diff//2) * 4
            self.assertListEqual(
                lines,
                ["    def f():\n", "        print(1)\n", "            x\n"],
            )

    def test_run_indent_no_change_if_zero_divisor(self: Self, /) -> None:
        """If no common indent (divisor=0), indent option does nothing."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "def f():\nprint(1)\n"  # all diff=0 so divisor=0
            f = self._write_text_file(tmpdir, "i.py", content)
            run(str(f), indent=4)
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["def f():\n", "print(1)\n"])

    def test_run_indent_dedent_to_zero(self: Self, /) -> None:
        """--indent 0 removes all leading spaces."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "    indented\n        more\n"
            f = self._write_text_file(tmpdir, "j.py", content)
            run(str(f), indent=0)
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["indented\n", "more\n"])

    def test_run_combination_indent_sort_empty(self: Self, /) -> None:
        """Test combined options: indent, unique+sort, empty in run order."""
        content: str
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "  b\n\n  a\n  b\n    c\n"
            f = self._write_text_file(tmpdir, "k.py", content)
            run(str(f), indent=2, sort=True, unique=True, empty=0)
            lines = self._read_lines(f)
            # after unique+sort+vstrip: "    c\n" sorts before "  a\n"
            self.assertListEqual(lines, ["    c\n", "  a\n", "  b\n"])

    def test_run_multiple_files_and_glob(self: Self, /) -> None:
        """Multiple patterns and globs process each file once."""
        f1: pathlib.Path
        f2: pathlib.Path
        f3: pathlib.Path
        sub: pathlib.Path
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            f1 = self._write_text_file(tmpdir, "m1.txt", "z\ny\n")
            f2 = self._write_text_file(tmpdir, "m2.txt", "x\n")
            sub = tmpdir / "sub"
            f3 = self._write_text_file(sub, "m3.txt", "w\n")
            # glob non-recursive misses sub, ** works with recursive
            run(str(tmpdir / "m*.txt"), str(tmpdir / "**/m3.txt"), sort=True)
            self.assertListEqual(self._read_lines(f1), ["y\n", "z\n"])
            self.assertListEqual(self._read_lines(f2), ["x\n"])
            self.assertListEqual(self._read_lines(f3), ["w\n"])

    def test_run_dedups_absfiles(self: Self, /) -> None:
        """Same file matched by multiple patterns processed only once."""
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            f = self._write_text_file(tmpdir, "n.txt", "line1\nline1\n")
            run(str(f), str(f), unique=True)
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["line1\n"])  # unique removed dup

    def test_run_skips_directories(self: Self, /) -> None:
        """Directory paths are skipped even if pattern matches."""
        f: pathlib.Path
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            (tmpdir / "dir").mkdir()
            f = self._write_text_file(tmpdir, "o.txt", "content\n")
            run(str(tmpdir / "*"))  # matches dir and o.txt
            self.assertListEqual(self._read_lines(f), ["content\n"])

    def test_main_calls_run_equivalent(self: Self, /) -> None:
        """main(args) equivalent to run for file processing."""
        f: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            f = self._write_text_file(tmpdir, "p.txt", "B\nA\n")
            with patch("importlib.metadata.version"):
                main(["--sort", str(f)])
            lines = self._read_lines(f)
            self.assertListEqual(lines, ["A\n", "B\n"])

    def test_main_version(self: Self, /) -> None:
        """--version prints version and exits 0."""
        code: int
        mock_version: MagicMock
        output: str
        stdout: io.StringIO
        with (
            patch("importlib.metadata.version") as mock_version,
            redirect_stdout(io.StringIO()) as stdout,
        ):
            mock_version.return_value = "0.1.0"
            try:
                code = main(["--version"])
            except BaseException as exc:
                self.assertIsNone(exc)
            else:
                self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("0.1.0", output)

    def test_main_help(self: Self, /) -> None:
        """--help prints usage and exits 0."""
        code: int
        output: str
        stdout: io.StringIO
        with (
            patch("importlib.metadata.version"),
            redirect_stdout(io.StringIO()) as stdout,
        ):
            try:
                code = main(["--help"])
            except BaseException as exc:
                self.assertIsNone(exc, None)
            else:
                self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("usage:", output.lower())
        self.assertIn("normalizes whitespace", output)

    def test_run_empty_file(self: Self, /) -> None:
        """Empty file stays empty."""
        f: pathlib.Path
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            f = self._write_text_file(tmpdir, "empty.txt", "")
            run(str(f), sort=True, unique=True, empty=0, indent=4)
            self.assertEqual(f.read_text(encoding="utf-8"), "")

    def test_run_only_blanks(self: Self, /) -> None:
        """Only-blank file becomes empty after vstrip."""
        f: pathlib.Path
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            f = self._write_text_file(tmpdir, "blanks.txt", "\n\n\n")
            run(str(f))
            self.assertEqual(f.read_text(encoding="utf-8"), "")

    def test_run_preserves_final_newline(self: Self, /) -> None:
        """Processed non-empty file ends with exactly one newline."""
        content: str
        f: pathlib.Path
        text: str
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            content = "last line without nl"
            f = self._write_text_file(tmpdir, "final.txt", content)
            run(str(f))
            text = f.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertNotIn("\n\n", text)  # no extra

    def test_run_with_at_file(self: Self, /) -> None:
        """fromfile_prefix @ allows args from file (argparse feature)."""
        argsfile: pathlib.Path
        datafile: pathlib.Path
        lines: list[str]
        tmp: str
        tmpdir: pathlib.Path
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            argsfile = self._write_text_file(
                tmpdir, "args.txt", "--sort\n--unique\n"
            )
            datafile = self._write_text_file(tmpdir, "data.txt", "z\nz\na\n")
            # main with @file
            with patch("importlib.metadata.version"):
                main([f"@{argsfile}", str(datafile)])
            lines = self._read_lines(datafile)
            self.assertListEqual(lines, ["a\n", "z\n"])


if __name__ == "__main__":
    unittest.main()
