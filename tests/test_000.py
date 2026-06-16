import os
import tempfile
import unittest
from typing import Any, Self

from jacobus import main, run

__all__ = ["TestRun"]


class TestRun(unittest.TestCase):
    def test_run_normalizes_whitespace(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")

            with open(path, "w") as f:
                f.write("\n\n    hello\n        world\n\n")

            run(path, indent=2)

            with open(path) as f:
                result = f.readlines()

            self.assertEqual(
                result,
                [
                    "  hello\n",
                    "    world\n",
                ],
            )

    def test_run_multiple_files_and_glob(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a = os.path.join(tmpdir, "a.txt")
            b = os.path.join(tmpdir, "b.txt")

            for path in (a, b):
                with open(path, "w") as f:
                    f.write("    x\n")

            run(os.path.join(tmpdir, "*.txt"), indent=4)

            for path in (a, b):
                with open(path) as f:
                    self.assertEqual(f.readlines(), ["    x\n"])

    def test_run_deduplicates_matches(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")

            with open(path, "w") as f:
                f.write("    x\n")

            run(path, os.path.join(tmpdir, "*.txt"), indent=2)

            with open(path) as f:
                self.assertEqual(f.readlines(), ["  x\n"])


if __name__ == "__main__":
    unittest.main()
