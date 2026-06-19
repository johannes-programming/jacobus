import os
import tempfile
import unittest
from typing import Any, Self

from jacobus import main

__all__ = ["TestJacobusMain"]


class TestJacobusMain(unittest.TestCase):
    def write(self: Self, path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def read(self: Self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_empty_file_stays_empty(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.txt")
            self.write(path, "")

            main([path])

            self.assertEqual(self.read(path), "")

    def test_rstrip_trims_trailing_spaces(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "a   \nb   \n")

            main([path])

            self.assertEqual(self.read(path), "a\nb\n")

    def test_vstrip_removes_outer_blank_lines(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "\n\nhello\nworld\n\n\n")

            main([path])

            self.assertEqual(self.read(path), "hello\nworld\n")

    def test_empty_limits_consecutive_blank_lines(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "a\n\n\n\nb\n")

            main(["--empty", "2", path])

            self.assertEqual(self.read(path), "a\n\n\nb\n")

    def test_empty_zero_removes_all_blank_lines(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "a\n\nb\n\nc\n")

            main(["--empty", "0", path])

            self.assertEqual(self.read(path), "a\nb\nc\n")

    def test_sort_lines(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "c\nb\na\n")

            main(["--sort", path])

            self.assertEqual(self.read(path), "a\nb\nc\n")

    def test_sort_with_blank_lines(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            self.write(path, "b\n\nc\na\n")

            main(["--sort", path])

            self.assertEqual(self.read(path), "a\nb\nc\n")

    def test_indent_reduction(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.py")
            self.write(path, "    a\n        b\n")

            main(["--indent", "2", path])

            self.assertEqual(self.read(path), "  a\n    b\n")

    def test_indent_preserved_without_flag(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.py")
            self.write(path, "    a\n        b\n")

            main([path])

            self.assertEqual(self.read(path), "    a\n        b\n")

    def test_combined_sort_empty_indent(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "combo.txt")
            self.write(path, "    z\n\n\n        y\n    x\n")

            main(["--sort", "--empty", "1", "--indent", "2", path])

            self.assertEqual(self.read(path), "    y\n  x\n  z\n")

    def test_recursive_glob(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "sub"))

            a = os.path.join(tmp, "a.txt")
            b = os.path.join(tmp, "sub", "b.txt")

            self.write(a, "z\n")
            self.write(b, "a\n")

            main(["--sort", os.path.join(tmp, "**", "*.txt")])

            self.assertEqual(self.read(a), "z\n")
            self.assertEqual(self.read(b), "a\n")

    def test_duplicate_matches_only_processed_once(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.txt")
            self.write(path, "b\na\n")

            main(["--sort", path, path])

            self.assertEqual(self.read(path), "a\nb\n")

    def test_all_blank_lines_becomes_empty(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "blank.txt")
            self.write(path, "\n\n\n")

            main([path])

            self.assertEqual(self.read(path), "")


if __name__ == "__main__":
    unittest.main()
