from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Self

from jacobus.core import run

__all__ = ["JacobusRunTests"]


class JacobusRunTests(unittest.TestCase):
    def test_strips_trailing_whitespace_and_outer_blank_lines(
        self: Self,
    ) -> None:
        root: Path
        target: Path
        tmp: str
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sample.txt"
            target.write_text(
                "\n\nalpha   \n\n beta\t\t\n\n", encoding="utf-8"
            )

            run(os.path.join(tmp, "*.txt"))

            self.assertEqual(
                target.read_text(encoding="utf-8"), "alpha\n\n beta\n"
            )

    def test_rescales_space_indentation_when_indent_is_given(
        self: Self,
    ) -> None:
        root: Path
        target: Path
        tmp: str
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sample.py"
            target.write_text("  alpha\n    beta\nplain\n", encoding="utf-8")

            run(os.path.join(tmp, "*.py"), indent=4)

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "    alpha\n        beta\nplain\n",
            )

    def test_unmatched_glob_does_not_touch_files(self: Self) -> None:
        root: Path
        tmp: str
        target: Path
        original: str
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sample.txt"
            original = "alpha   \n"
            target.write_text(original, encoding="utf-8")

            run(os.path.join(tmp, "*.py"))

            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_binary_or_invalid_utf8_file_is_left_unchanged_on_decode_error(
        self: Self,
    ) -> None:
        original: Any
        root: Path
        target: Path
        tmp: str
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "bad.bin"
            original = b"\xff\xfe\x00not utf-8"
            target.write_bytes(original)

            with self.assertRaises(UnicodeDecodeError):
                run(str(target))

            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
