import os
import tempfile
import unittest
from typing import Any, Self

from jacobus import main

__all__ = ["TestJacobusMain"]


class TestJacobusMain(unittest.TestCase):
    def write(self: Self, path: Any, content: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def read(self: Self, path: Any) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_empty_file(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.txt")
            self.write(path, "")

            main([path])

            self.assertEqual(self.read(path), "")

    def test_trim_blank_lines_and_trailing_spaces(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "\n\nhello   \nworld   \n\n\n")

            main([path])

            self.assertEqual(self.read(path), "hello\nworld\n")

    def test_preserve_indent_without_flag(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.py")
            self.write(path, "    a\n        b\n")

            main([path])

            self.assertEqual(self.read(path), "    a\n        b\n")

    def test_change_indent(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.py")
            self.write(path, "    a\n        b\n")

            main(["--indent", "2", path])

            self.assertEqual(self.read(path), "  a\n    b\n")

    def test_multiple_files_via_glob(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "a.txt")
            b = os.path.join(tmp, "b.txt")

            self.write(a, "\nfoo   \n")
            self.write(b, "\nbar   \n")

            main([os.path.join(tmp, "*.txt")])

            self.assertEqual(self.read(a), "foo\n")
            self.assertEqual(self.read(b), "bar\n")

    def test_duplicate_globs_do_not_break(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.txt")
            self.write(path, "hello   \n")

            main([path, path])

            self.assertEqual(self.read(path), "hello\n")


if __name__ == "__main__":
    unittest.main()
